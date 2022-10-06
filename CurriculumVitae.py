from dataclasses import dataclass, field
from abc import abstractmethod
from itertools import count
from re import sub
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, Template
import cv_host
import os, subprocess
import json
import hashlib, urllib, skill_cat
import abc
import uuid


from datetime import date

DEFAULT_DENSITY_THRESHOLD=0


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

    @staticmethod
    def get_template_prefix(classname:str, alt_template_prefixes:dict[str,str]={}, **kwargs) -> str:
        return alt_template_prefixes.get(classname, alt_template_prefixes.get("*", ""))

    @staticmethod
    def get_template(classname, **kwargs) -> Template:
        prefix = _NestedHTML.get_template_prefix(classname, **kwargs)
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
    must_render:bool=False
    cost:float = 1.0

    def get_weight(self, **kwargs) -> float:
        return 0

    def get_cost(self, **kwargs) -> float:
        return self.cost

    def _should_render(self, **kwargs) -> bool:
        if self.must_render:
            return True
        if kwargs.get("should_render_all", False):
            return True
        elif (own_cost := self.get_cost(**kwargs)) == 0:
            return True # It's costless to render, therefore render
        else:
            return (self.get_weight(**kwargs) / own_cost) > kwargs.get("density_threshold", DEFAULT_DENSITY_THRESHOLD)

    def __repr_html__(self, **kwargs):
        if self._should_render(**kwargs):

            # Replace existing cost and weight from higher calls,
            #   or just add them if they aren't present.
            kwargs.update({
                "cnh_cost":self.get_cost(**kwargs),
                "cnh_weight":self.get_weight(**kwargs)
            })

            kwargs["cnh_density"] = kwargs["cnh_weight"] / (kwargs["cnh_cost"] if kwargs["cnh_cost"] != 0 else 1)

            kwargs["cnh_met_threshold"] = kwargs["cnh_density"] > kwargs.get("density_threshold", DEFAULT_DENSITY_THRESHOLD)
            return super().__repr_html__(**kwargs)
        else:
            return ""

@dataclass(kw_only=True)
class _Nested_Conditional(_NestedHTML):

    def get_contained_weight(self, **kwargs) -> float:
        return sum([child.get_weight(**kwargs) for child in self._get_conditional_children(**kwargs) if child._should_render(**kwargs)])
    
    def get_contained_cost(self, **kwargs) -> float:
        return sum([child.get_cost(**kwargs) for child in self._get_conditional_children(**kwargs) if child._should_render(**kwargs)])

    @abstractmethod
    def _get_conditional_children(self, **kwargs) -> list['_Conditional_nHTML']:
        pass



@dataclass(kw_only=True)
class _Nested_Conditional_nHTML(_Conditional_nHTML, _Nested_Conditional):

    # Class is a candidate for a mapreduce utility method

    def get_weight(self, **kwargs) -> float:
        # Sometimes, we choose to render everything, reguardless of its computed properties.
        # In those instances, we still want the numerical values for those properties to reflect the configuration we provided.
        # So, we compute weight as though we *never* have `should_render_all==True`
        kwargs['should_render_all']=False
        return super().get_weight(**kwargs) + self.get_contained_weight(**kwargs)
    
    def get_cost(self, **kwargs) -> float:
        # Sometimes, we choose to render everything, reguardless of its computed properties.
        # In those instances, we still want the numerical values for those properties to reflect the configuration we provided.
        # So, we compute cost as though we *never* have `should_render_all==True`
        kwargs['should_render_all']=False
        return super().get_cost(**kwargs) + self.get_contained_cost(**kwargs)

@dataclass(kw_only=True)
class Skill(_Conditional_nHTML):
    synonym_base:str
    name:str
    num_instances:int
    weight:float
    share_of_job:float=field(default=None)

    def __hash__(self):
        return hash(self.name.lower())

    def get_weight(self, **kwargs) -> float:
        return self.weight
    
    def get_cost(self, **kwargs) -> float:
        # Note: The 'cost' of a skill is interpreted in a few conceptual ways,
        #   which get handled in the same computational way.
        # 1. The 'cost' as space taken up in the final product.
        # 2. The 'cost' as an indication of the variety of ideas something expresses.


        # Why not just return `kwargs.get('skill_cost', super().get_cost(**kwargs))`?
        # Great question! This approach falls back to the default when 'skill_cost' is provided with a value of `None`.
        own_cost = kwargs.get("skill_cost", None)
        return super().get_cost(**kwargs) if own_cost is None else own_cost
    
    def _should_render(self, **kwargs) -> bool:
        # Skills have a special kwarg ('skills_render_by_weight') indicating they should
        #     ignore their cost and render based soley on their weight.
        # That gets evaluated here.
        if kwargs.get("should_render_all", False):
            return True
        elif kwargs.get("should_render_all_skills", False):
            return True
        elif kwargs.get("skills_render_by_weight", False):
            return self.get_weight(**kwargs) > kwargs.get("density_threshold", DEFAULT_DENSITY_THRESHOLD)
        else:
            return super()._should_render(**kwargs)
        
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
    cost:float = 0
    
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
                    weight=0,
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


    def _should_render(self, **kwargs) -> bool:
        # This is just an intermediate storage. It should always 'render'
        return True

    # In normal use, this method should *not* get called.
    # Instead, SkillSynonymGroup should automatically get skipped by containing object calling `skill_div` on a list of `SkillSynonymGroup`s.
    # However, the method complies with expectations and is safe to use.
    def __repr_html__(self, **kwargs):
        return skills_div([self], **kwargs)
    

@dataclass(kw_only=True)
class ContactInfo(_NestedHTML):
    email:str = None
    phone:str = None
    link:str = None
    link2:str = None # Ought to be lists or dicts per group


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

    # This ought to be a 'line-weighted conditional' class
    chars_per_line:float = 80.0
    cost:float = 0

    def get_cost(self, **kwargs) -> float:
        return super().get_cost(**kwargs) + max(1, round(len(self.headline)/self.chars_per_line, 1))

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
    cost:float = 2
    
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
    cost:float = 3

    def __repr__(self) -> str:
        return f"<Occupation '{self.title}' ({self.headline} at {self.location} under {self.supervisor}) with {len(self.achievements)} achievements and {len(self.sub_tasks)} subtasks>"

@dataclass(kw_only=True)
class Certification(Achievement):
    name:str
    issuer:str
    issue_date:date
    website:str = None
    confirmation_info:dict = field(default_factory=dict)
    cost:float = 1

    def get_cost(self, **kwargs) -> float:
        return super().get_cost(**kwargs) + (1 if self.website else 0) + (1 if self.confirmation_info else 0)
    

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


    def _get_conditional_children(self, *args, **kwargs) -> list['_Conditional_nHTML']:
        return self.education + self.employment + self.projects + list(self.skills)
    
    def write_html_to_file(self, filepath="docs/resume.html", **kwargs):
        with open(filepath, "w+") as f:
            f.write(self.__repr_html__(**kwargs))

    def export_pdf(self, pdf_fpath, html_docs_subpath:str=None, threadsafe=True, **kwargs):
        if html_docs_subpath is None:
            os.makedirs("docs/pdf_sources/tmp", exist_ok=True)
            html_docs_subpath = f"pdf_sources/tmp/{uuid.uuid4() if threadsafe else 'export_pdf'}.html"
        
        self.write_html_to_file(filepath=f"docs/{html_docs_subpath}", **kwargs)
        
        # Run a google-chrome headless subprocess to export
        process = subprocess.run(f"google-chrome --headless --run-all-compositor-stages-before-draw --print-to-pdf={pdf_fpath} 'http://localhost:8000/{html_docs_subpath}'", shell=True, capture_output=True)
        
        if process.returncode:
            raise Exception(f"Chrome pdf export\n\t{process.args}\nfailed with code {process.returncode}.\nStdout was:\n{process.stdout}\nStderr was:\n{process.stderr}")
        
    def export_fitted_pdf(self, pdf_fpath, page_goal=1, lowest_threshold=0, highest_threshold=0.005, threadsafe=True, max_iters=10, **kwargs):
        # The goal is to fill the smallest number of pages, where that number is equal to or greater than the page goal.

        # Define a naming and exporting utility
        # This could be modified to not reuse names, so that iterations stick around.
        def named_export(small=False, density_threshold=lowest_threshold, index=0):
            name = pdf_fpath#+f".{index}.{'small' if small else 'normal'}.d{density_threshold}.pdf"
            #print(name)
            self.export_pdf(name, goal_small=small, density_threshold=density_threshold, threadsafe=threadsafe, **kwargs)
            return {"name":name, "pages":count_pages_in_pdf(name)}

        # Define the smallest and largest possible resumes within the bounds given
        largebound = lowest_threshold
        smallbound = highest_threshold

        small_file= named_export(small=True, density_threshold=smallbound, index='!')
        xlarge_file = named_export(small=False, density_threshold=largebound, index='!')

        # If our entire configuration space varies by less than one page, or is within acceptable pages,
        if xlarge_file["pages"] == small_file["pages"] or (xlarge_file["pages"] <= page_goal):
            print("Iteration not necessary - largest is valid. Taking most preferred configuration.")
            return dict(small=False, density_threshold=largebound, **xlarge_file) # Take the best (largest) configuration within that page


        large_file = named_export(small=True, density_threshold=largebound, index='!')
        
        if large_file["pages"] == small_file["pages"]:
            # The largebound w/ small text is the same num. of pages as the smallbound
            print("Page count does not vary with density. Taking largebound density with small text.")
            return dict(small=True, density_threshold=largebound, **large_file)
        
        print("Must traverse configuration space.")

        # Otherwise, keep defining our search space
        use_small = True

        if large_file["pages"] == small_file["pages"]: 
            effective_page_goal = large_file["pages"]
        else:
            effective_page_goal = page_goal

        # Iteratively find the most desirable config
        for iterations in range(max_iters):
            new_est = (largebound+smallbound)/2.0
            new_file = named_export(small=use_small, density_threshold=new_est, index=iterations)
            if new_file["pages"] > effective_page_goal:
                largebound = new_est
            else:
                smallbound = new_est
                small_file = new_file

        # Because content appears and rolls in blocks, it's possible a large-format (ie not-small) resume would fit on the same number of pages
        if use_small:
            large_file = named_export(small=False, density_threshold=smallbound, index='?')
            use_small = large_file["pages"] > small_file["pages"]

        return dict(small=use_small, density_threshold=smallbound, **named_export(small=use_small, density_threshold=smallbound, index='_'))


    def host(self, *args, **kwargs):
        self.write_html_to_file(*args, **kwargs)
        cv_host.start_hosting()


def count_pages_in_pdf(pdf_fpath):
    # This is a *very* trusting method
    # And I haven't tested it at all.
    return int(subprocess.run(
        "strings < "+pdf_fpath+" | grep -oP '(?<=/Count )\d{1,}' | sort -rn | head -n 1", 
        shell=True, 
        capture_output=True
    ).stdout.strip())


@dataclass(kw_only=True)
class JobListing:
    name:str
    skill_text_weights:dict[str,dict[str,dict[str, float]]] = field(default_factory=dict)
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

