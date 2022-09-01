from dataclasses import dataclass, field
from abc import abstractmethod
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import cv_host


from datetime import date

def _list_to_ul(listed:list['_NestedHTML'], depth=1, **kwargs):
    if not listed:
        return ""
    listed = map(lambda e: e.__repr_html__(depth=depth, **kwargs), 
                    filter(lambda e: e._compare_exporting(kwargs.get("jinja2_render_args", dict())), listed))

    return _NestedHTML.get_template("_list_to_ul", **kwargs).render(
        listed=listed,
        depth=depth,
        **kwargs
    )

@dataclass(kw_only=True)
class _NestedHTML():
    _template_env = Environment(loader=FileSystemLoader("templates/"))
    consumed_depth:int = 1
    exports:list = field(default_factory=list)

    @staticmethod
    def get_template(classname, alt_template_prefixes={}, **kwargs):
        prefix = alt_template_prefixes.get(classname, alt_template_prefixes.get("*", ""))

        try:
            return _NestedHTML._template_env.get_template(prefix + classname + ".html")
        except TemplateNotFound:
            return _NestedHTML._template_env.get_template(classname + ".html")


    def _compare_exporting(self, jinja2_render_args:dict):
        if hasattr(self, "exports") and len(self.exports): # For some reason, Skill objects don't have an 'exports' attribute, but do have consumed_depth. WTF. I think I'm modifying a reference somewhere.
            if "exports" in jinja2_render_args:
                # return jinja2_render_args["export"] in self.exports
                return bool(set(jinja2_render_args["exports"]) & set(self.exports))
            else:
                return True
        else:
            return True

    @abstractmethod
    def __repr_html__(self, depth=1, **kwargs):
        kwargs.setdefault("jinja2_render_args", dict())

        if self._compare_exporting(kwargs["jinja2_render_args"]):
            obj_attrs = {}
            for attr_name, attr in self.__dict__.copy().items():
                # print("\t"*depth + f"Class {self.__class__.__name__} converting attr {attr_name}: '{attr}':")

                attr = list(attr) if isinstance(attr, set) else attr

                match attr:
                    case _NestedHTML():
                        attr = attr.__repr_html__(depth=depth+self.consumed_depth, **kwargs)

                    case [*skills] if len(skills) > 0 and all(isinstance(skill, Skill) for skill in skills):
                        attr = skills_div(skills, depth=depth+self.consumed_depth, **kwargs)

                    case [*nHTMLs] if len(nHTMLs) > 0 and all(isinstance(nHTML, _NestedHTML) for nHTML in nHTMLs):
                        attr = _list_to_ul(nHTMLs, depth=depth+self.consumed_depth, **kwargs)
                    
                    case str() as string_attr:
                        obj_attrs[f"clean_{attr_name.replace(' ', '_')}"] = string_attr.lower().replace(" ", "_")

                # print("\t"*depth + f"Class {self.__class__.__name__} converted  attr {attr_name} to '{attr}'")

                obj_attrs[attr_name] = attr
            obj_attrs.update(kwargs)



            return _NestedHTML.get_template(self.__class__.__name__, **kwargs).render(
                depth=depth, 
                className=self.__class__.__name__, 
                **obj_attrs,
            )
        else:
            return ""


@dataclass(kw_only=True)
class _NamedSingleton:
    _NS_by_class = dict()
    _count_by_class = dict()
    name:str
    def __new__(cls, name, *args, **kwargs):
        """Enforce all NamedSingletons with identical names and classes refer to the same object."""
        # If `name.lower()` is a new name for the class, continue calling super().__new__ to construct a new instance
        #   and assign that instance to be the owner of name.lower() in the class's dict.
        # Else, return the pre-existing instance from the class-wide dict.

        # Why do I feel comfortable dynamically constructing singletons?
        #   Because this tool is a proof of concept. If this were to end up on multi-threaded code,
        #   it should have already been converted into a Relational Database, 
        #   and Type().name would become a unique column.

        _NamedSingleton._count_by_class.setdefault(cls, dict()).setdefault(name.lower(), 0)
        _NamedSingleton._count_by_class[cls][name.lower()] += 1

        return _NamedSingleton._NS_by_class.setdefault(cls, dict()).setdefault(name.lower(), super().__new__(cls))

    def __hash__(self):
        return hash(self.name)
    
    def _get_popularity(self, popularity_dict=None, **kwargs):
        lname = self.name.lower()
        if popularity_dict is None:
            popularity = 1
        else:
            popularity = popularity_dict.get(self.__class__, dict()).get(lname, 0)
        instances = _NamedSingleton._count_by_class[self.__class__][lname]

        popularity_tuple = (popularity, instances, lname)
        # print(popularity_tuple)
        return popularity_tuple


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

class Skill(_NamedSingleton, _NestedHTML):
    pass

def Skills(*args):
    return [Skill(name=skill) for skill in args]

def skills_div(skills_list:list[Skill], depth=1, suppress_popularity_threshold=-1e10, **kwargs):
    if not skills_list:
        return
    
    popularities_and_skills = filter(
        lambda ps: ps[0][0] > suppress_popularity_threshold, 
        [(skill._get_popularity(**kwargs), skill) for skill in skills_list])

    return _NestedHTML.get_template("_skills_div", **kwargs).render(
        skills=map(lambda s: s[1].__repr_html__(depth=depth, **kwargs),
                    sorted(popularities_and_skills, reverse=True)), **kwargs)

@dataclass(kw_only=True)
class Achievement(_NestedHTML):
    headline:str
    skills:list[Skill] = field(default_factory=list)

@dataclass(kw_only=True)
class Between(_NestedHTML):
    start:date
    end:date = None

@dataclass(kw_only=True)
class Effort(_NestedHTML):
    title:str
    headline:str
    website:str = None

    achievements:list[Achievement] = field(default_factory=list)
    sub_tasks:list['Effort'] = field(default_factory=list)

@dataclass(kw_only=True)
class Occupation(Effort):
    timespan:Between
    subtitle:str
    supervisor:Person = None
    location:str = None

@dataclass(kw_only=True)
class Certification(_NamedSingleton, Achievement):
    issuer:str
    issue_date:date
    website:str = None
    confirmation_info:dict = field(default_factory=dict)

    def __hash__(self):
        return _NamedSingleton.__hash__(self)

@dataclass(kw_only=True)
class Resume(_NestedHTML):
    person:Person
    headline:str
    # about:dict
    education:list[Occupation] = field(default_factory=list)
    employment:list[Occupation] = field(default_factory=list)
    projects:list[Effort] = field(default_factory=list)
    certifications:set[Certification] = field(default_factory=set)
    skills:set[Skill] = field(default_factory=set)
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

    def Certification(self, *args, **kwargs):
        """Construct a certification and store it in this resume."""
        new = Certification(*args, **kwargs)
        self.certifications.add(new)
        return new
    
    def Skill(self, *args, **kwargs):
        """Construct a skill and store it in this resume."""
        new = Skill(*args, **kwargs)
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

    def host(self, *args, **kwargs):
        self.write_html_to_file(*args, **kwargs)
        cv_host.start_hosting()


@dataclass
class JobListing:
    name:str
    skills_ranking:dict[str] = field(default_factory=dict)
    exports:list[str] = field(default_factory=list)
    stylesheet:str = "lighttheme"
    jinja2_render_args:dict = field(default_factory=dict)

    def export(self, resume:Resume):
        # Write the HTML-based hosted resume
        resume.write_html_to_file(
            filepath=f"docs/resumes/{self.name}.html",
            jinja2_render_args = {
                "exports": self.exports,
                "stylesheet":self.stylesheet,
                **self.jinja2_render_args
            },
            popularity_dict = {Skill: self.skills_ranking}
        )

        # Write the to-be-a-pdf resume
        resume.write_html_to_file(
            filepath=f"docs/pdf_sources/{self.name}.html",
            alt_template_prefixes = {"*": "pdf"},
            jinja2_render_args = {
                "exports": self.exports,
                "resume_link": f"http://fractalmachini.st/resumes/{self.name}.html",
                "stylesheet":self.stylesheet,
                **self.jinja2_render_args
            },
            popularity_dict = {Skill: self.skills_ranking}
        )
        return f"http://fractalmachini.st/pdf_sources/{self.name}.html"

