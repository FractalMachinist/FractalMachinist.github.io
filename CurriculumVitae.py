from dataclasses import dataclass, field
from abc import abstractmethod
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, Template
import cv_host
import os
import json
import hashlib, urllib, skill_cat
import abc


from datetime import date


def _grouper(to_group:list['_NestedHTML'], template_name, group_arg_name, **kwargs):
    groupies = list(filter(None, map(lambda groupie: groupie.__repr_html__(**kwargs), to_group)))
    if not len(groupies):
        return ""
        
    return _NestedHTML.get_template(template_name, **kwargs).render(
        **kwargs,
        **{group_arg_name: groupies}
    )

def _list_to_ul(listed:list['_NestedHTML'], **kwargs):
    return _grouper(listed, '_list_to_ul', 'listed', **kwargs)

def skills_div(skill_syn_groups:list['SkillSynonymGroup'], **kwargs):
    skills = sorted(
        [skill for skill_syn_group in skill_syn_groups for skill in skill_syn_group._get_conditional_children(**kwargs)],
        key = lambda skl: skl._sort_key(**kwargs)
    )
    return _grouper(skills, '_skills_div', 'skills', **kwargs)


def Skills(*args):
    return [SkillSynonymGroup(name=skill) for skill in args]



@dataclass(kw_only=True)
class _NestedHTML():
    _template_env = Environment(loader=FileSystemLoader("templates/"))
    consumed_depth:int = 1
    exports:list = field(default_factory=list)

    @staticmethod
    def get_template(classname, alt_template_prefixes={}, **kwargs) -> Template:
        prefix = alt_template_prefixes.get(classname, alt_template_prefixes.get("*", ""))

        try:
            return _NestedHTML._template_env.get_template(prefix + classname + ".html")
        except TemplateNotFound:
            return _NestedHTML._template_env.get_template(classname + ".html")


    @abstractmethod
    def __repr_html__(self, depth=1, **kwargs) -> str:
        obj_attrs = {}
        for attr_name, attr in self.__dict__.copy().items():
            if kwargs.get("debug", False):
                print(">\t"*depth + f"Class {self.__class__.__name__} converting attr '{attr_name}': '{attr}':")

            attr = list(attr) if isinstance(attr, set) else attr

            match attr:
                case _NestedHTML():
                    attr = attr.__repr_html__(depth=depth+self.consumed_depth, **kwargs)

                case [*nHTMLs] if all(isinstance(nHTML, _NestedHTML) for nHTML in nHTMLs):
                    grouper = skills_div if all(isinstance(nHTML, SkillSynonymGroup) for nHTML in nHTMLs) else _list_to_ul
                    attr = grouper(nHTMLs, depth=depth+self.consumed_depth, **kwargs)
                
                case str() as string_attr if len(attr):
                    obj_attrs[f"clean_{attr_name.replace(' ', '_')}"] = string_attr.lower().replace(" ", "_")



            if attr != "":
                obj_attrs[attr_name] = attr
        obj_attrs.update(kwargs)

        product = _NestedHTML.get_template(self.__class__.__name__, **kwargs).render(
            depth=depth, 
            className=self.__class__.__name__, 
            **obj_attrs,
        )

        if kwargs.get("debug", False) and isinstance(self, Effort):
            print(f"<\t"*depth + f"Occupation {self.title} converted to '{product}'")
        return product


@dataclass(kw_only=True)
class _Conditional_nHTML(_NestedHTML):

    # @abstractmethod
    # def _get_share(self, **kwargs) -> float:
    #     pass

    @abstractmethod
    def _should_render(self,**kwargs) -> bool:
        pass

    def __repr_html__(self, **kwargs):
        if kwargs.get("should_render_all", False) or self._should_render(**kwargs):
            return super().__repr_html__(**kwargs)
        else:
            return ""

@dataclass(kw_only=True)
class _Nested_Conditional(_NestedHTML):
    @abstractmethod
    def _get_conditional_children(self, **kwargs) -> list['_Conditional_nHTML']:
        pass



@dataclass(kw_only=True)
class _Nested_Conditional_nHTML(_Conditional_nHTML, _Nested_Conditional):

    # def _get_share(self, **kwargs) -> float:
    #     return sum([child._get_share(**kwargs) for child in self._get_conditional_children(**kwargs)])

    def _should_render(self,**kwargs) -> bool:
        # return self._get_share(**kwargs) > 0
        return any(child._should_render(**kwargs) for child in self._get_conditional_children(**kwargs))

@dataclass(kw_only=True)
class Skill(_Conditional_nHTML):
    synonym_base:str
    name:str
    num_instances:int
    weight:float
    share_of_job:float=field(default=None)

    def __hash__(self):
        return hash(self.name.lower())

    # def _get_weight(self, **kwargs) -> float:
    #     return self.weight

    def _should_render(self, **kwargs) -> bool:
        return self.weight > 0
    
    def _sort_key(self, **kwargs) -> tuple:
        return (
            None if self.weight is None else -self.weight,
            None if self.num_instances is None else -self.num_instances,
            self.name.lower()
        )

@dataclass(kw_only=True)
class SkillSynonymGroup(_Nested_Conditional_nHTML):
    _instances_and_counts = dict()
    name:str
    
    def __new__(cls, name, *args, **kwargs):
        # Why am I comfortable making singleton instances at runtime?
        # Because this is a prototype, and if we wanted it to be bigger, we'd make a database with a uniqueness constraint.
        instance, old_count = SkillSynonymGroup._instances_and_counts.setdefault(name.lower(), (super().__new__(cls), 0))
        SkillSynonymGroup._instances_and_counts[name.lower()] = (instance, old_count + 1)
        return instance

    def __hash__(self):
        return hash(self.name.lower())

    def get_num_instances(self):
        return self._instances_and_counts[self.name.lower()][1]
        
    def _get_conditional_children(self, skill_text_weights:dict[str,dict[str,dict[str, float]]]={}, **kwargs) -> list['_Conditional_nHTML']:
        if len(skill_text_weights) == 0:
            return [
                Skill(
                    synonym_base=self.name,
                    name=self.name,
                    num_instances=self.get_num_instances(),
                    weight=None,
                    share_of_job=None
                )
            ]
        else:
            return [
                Skill(
                    synonym_base=self.name, 
                    name=name, 
                    num_instances=self.get_num_instances(),
                    weight=data["skill weight"],
                    share_of_job=data["share of job"]
                ) for name, data in skill_text_weights.get(self.name.lower(), {}).items()
            ]


    # In normal use, this method should *not* get called.
    # Instead, SkillSynonymGroup should automatically get skipped by a higher object calling `skill_div` on its own list of skills.
    # However, the method is compliant.
    def __repr_html__(self, **kwargs):
        return skills_div([self], **kwargs)
    

@dataclass(kw_only=True)
class ContactInfo(_NestedHTML):
    email:str = None
    phone:str = None
    link:str = None
    link2:str = None # It's an awful hack


@dataclass(kw_only=True)
class Person(_NestedHTML):
    name:str
    pronouns:str
    contact_info:ContactInfo


@dataclass(kw_only=True)
class Achievement(_Nested_Conditional_nHTML):
    headline:str
    skills:list[SkillSynonymGroup] = field(default_factory=list)
    portfolio_link:str = None

    def _get_conditional_children(self, *args, **kwargs) -> list['_Conditional_nHTML']:
        return self.skills
    
    def __repr__(self) -> str:
        return f"<Achievement '{self.headline}' with {len(self.skills)} skills and {'a' if self.portfolio_link is not None else 'no'} portfolio link>"

@dataclass(kw_only=True)
class Between(_NestedHTML):
    start:date
    end:date = None

@dataclass(kw_only=True)
class Effort(_Nested_Conditional_nHTML):
    title:str
    headline:str
    website:str = None
    
    skills:list[SkillSynonymGroup] = field(default_factory=list)

    achievements:list[Achievement] = field(default_factory=list)
    sub_tasks:list['Effort'] = field(default_factory=list)

    def _get_conditional_children(self, *args, **kwargs) -> list['_Conditional_nHTML']:
        return self.achievements + self.sub_tasks + self.skills
    
    def __repr__(self) -> str:
        return f"<Effort '{self.title}' ({self.headline}) with {len(self.achievements)} achievements and {len(self.sub_tasks)} subtasks>"

@dataclass(kw_only=True)
class Occupation(Effort):
    timespan:Between
    subtitle:str
    supervisor:Person = None
    location:str = None

    def __repr__(self) -> str:
        return f"<Occupation '{self.title}' ({self.headline} at {self.location} under {self.supervisor}) with {len(self.achievements)} achievements and {len(self.sub_tasks)} subtasks>"

@dataclass(kw_only=True)
class Certification(Achievement):
    name:str
    issuer:str
    issue_date:date
    website:str = None
    confirmation_info:dict = field(default_factory=dict)

@dataclass(kw_only=True)
class Resume(_Nested_Conditional):
    person:Person
    headline:str
    # about:dict
    education:list[Occupation] = field(default_factory=list)
    employment:list[Occupation] = field(default_factory=list)
    projects:list[Effort] = field(default_factory=list)
    skills:set[SkillSynonymGroup] = field(default_factory=set)
    consumed_depth:int = 2


    # Why are these methods here?
    #   I want the resume as a whole to be able to manage all skills and certifications it contains, 
    #       but I also want skills and certifications to exist as children of other types.
    #   A strictly-typed language with private fields could enforce a typing scheme where objects must expose a
    #       method which searches themselves for skills/certifications.
    #   However, without strict typing or private variables, a child object might be subclassed to add new
    #       attributes which contain skills or certifications, and we might not get a subclassed method to find them.
    #   Therefore, the "search the children" approach requires flood-searching, or just ~hoping~ the children are
    #       the right type and haven't been subclassed to add new places for Skills and Certifications to be.
    #
    #   Alternatively, we could ask the user to, by default, instantiate Skill and Certification objects via methods provided
    #       by the resume they want them to be a part of.
    #   This approach is more transparent to the user, with the downside of double-referencing the skills and certs,
    #       and obfuscating how to add objects to multiple resumes.

    
    def Skill(self, *args, **kwargs):
        """Construct a skill and store it in this resume."""
        new = SkillSynonymGroup(*args, **kwargs)
        self.skills.add(new)
        return new
    
    def Skills(self, *args, **kwargs):
        """Construct multiple skills and store them in this resume."""
        new = Skills(*args, **kwargs)
        self.skills.update(new)
        return new


    def write_html_to_file(self, filepath="docs/resume.html", **kwargs):
        with open(filepath, "w+") as f:
            f.write(self.__repr_html__(**kwargs))

    def _get_conditional_children(self, *args, **kwargs) -> list['_Conditional_nHTML']:
        return self.education + self.employment + self.projects + list(self.skills)

    def host(self, *args, **kwargs):
        self.write_html_to_file(*args, **kwargs)
        cv_host.start_hosting()


@dataclass(kw_only=True)
class JobListing:
    name:str
    skill_text_weights:dict[str,float] = field(default_factory=dict)
    exports:list[str] = field(default_factory=list)
    stylesheet:str = "lighttheme"


    def export(self, resume:Resume, public_name:str=None, **kwargs):
        # Write the HTML-based hosted resume
        # name = urllib.parse.quote(self.name)
        if self.name == "index":
            public_name = self.name
            private_name = self.name

            public_path = f"resumes/{public_name}"
            private_path= f"pdf_sources/{private_name}"
        else:
            if public_name is None:
                public_name = hashlib.md5(self.name.encode()).hexdigest()
            else:
                public_name = urllib.parse.quote(public_name)
            private_name = self.name

            public_path = f"resumes/{public_name}"
            private_path= f"pdf_sources/{private_name}/Zach_Allen_Resume"

            os.makedirs(f"docs/pdf_sources/{private_name}", exist_ok=True)

        

        urlsafe_private_path = urllib.parse.quote(private_path)
        
        # Write the to-be-public resume
        publish_args = {
            "filepath":f"docs/{public_path}.html",
            "stylesheet":self.stylesheet,
            "skill_text_weights":self.skill_text_weights}
        publish_args.update(kwargs)
        resume.write_html_to_file(**publish_args)

        # Write the to-be-a-pdf resume
        pdf_args = {
            "filepath":f"docs/{private_path}.html",
            "alt_template_prefixes":{"*": "pdf"},
            "resume_link": f"http://fractalmachini.st/{public_path}.html",
            "stylesheet":self.stylesheet,
            "skill_text_weights":self.skill_text_weights}
        pdf_args.update(kwargs)
        resume.write_html_to_file(**pdf_args)

        return urlsafe_private_path

