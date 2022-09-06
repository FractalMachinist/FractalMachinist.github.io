from dataclasses import dataclass, field
from abc import abstractmethod
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import cv_host
import os


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

def skills_div(skills:list['Skill'], **kwargs):
    return _grouper(sorted(skills, key=lambda skl: skl._get_popularity(**kwargs), reverse=True), '_skills_div', 'skills', **kwargs)


def Skills(*args):
    return [Skill(name=skill) for skill in args]



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


    def _should_render(self, jinja2_render_args:dict={}, **kwargs):
        j2_exports = jinja2_render_args.get("exports", [])

        if not self.exports or not j2_exports: # If any of them are empty or undefined:
            return True
        else:
            return bool(set(j2_exports) & set(self.exports))
            


    @abstractmethod
    def __repr_html__(self, depth=1, **kwargs):
        if self._should_render(**kwargs):
            obj_attrs = {}
            for attr_name, attr in self.__dict__.copy().items():
                if kwargs.get("debug", False):
                    print(">\t"*depth + f"Class {self.__class__.__name__} converting attr '{attr_name}': '{attr}':")

                attr = list(attr) if isinstance(attr, set) else attr

                match attr:
                    case _NestedHTML():
                        attr = attr.__repr_html__(depth=depth+self.consumed_depth, **kwargs)

                    case [*nHTMLs] if all(isinstance(nHTML, _NestedHTML) for nHTML in nHTMLs):
                        grouper = skills_div if all(isinstance(nHTML, Skill) for nHTML in nHTMLs) else _list_to_ul
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
        else:
            if kwargs.get("debug", False) and isinstance(self, Effort):
                print(f"<\t"*depth + f"Occupation {self.title} converted to ''")
            return ""


@dataclass(kw_only=True)
class Skill(_NestedHTML):
    _instances_and_counts = dict()
    name:str

    @staticmethod
    def _clean_name(name):
        return name.lower()

    def __new__(cls, name, *args, **kwargs):
        # Why am I comfortable making singleton instances at runtime?
        # Because this is a prototype, and if we wanted it to be bigger, we'd make a database with a uniqueness constraint.
        instance, count = Skill._instances_and_counts.setdefault(cls._clean_name(name), (super().__new__(cls), 0))
        count += 1
        return instance

    def __hash__(self):
        return hash(self._clean_name(self.name))

    def _get_popularity(self, popularity_dict:dict={}, **kwargs):
        clean_name = self._clean_name(self.name)
        instances = self._instances_and_counts[clean_name][1]
        popularity = popularity_dict.get(clean_name, 0)
        
        popularity_tuple = (popularity, instances, clean_name)
        return popularity_tuple
    
    def _should_render(self, suppress_popularity_threshold=(0, 0, ""), **kwargs):
        # If no popularity dict is given, or if an empty popularity dict is given,
        # assume every skill passes the popularity test.
        if kwargs.get("popularity_dict", False):
            p = self._get_popularity(**kwargs) > suppress_popularity_threshold

            if kwargs.get("debug", False):
                print(f"{'will' if p else 'will not'} render Skill {self.name}.")
            return p
        else:
            return self._get_popularity(**kwargs)[1:] > suppress_popularity_threshold[1:]


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
class Certification(Achievement):
    name:str
    issuer:str
    issue_date:date
    website:str = None
    confirmation_info:dict = field(default_factory=dict)

@dataclass(kw_only=True)
class Resume(_NestedHTML):
    person:Person
    headline:str
    # about:dict
    education:list[Occupation] = field(default_factory=list)
    employment:list[Occupation] = field(default_factory=list)
    projects:list[Effort] = field(default_factory=list)
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

categories = {
    "ML":     {"TensorFlow", 
               "Feature Engineering",
               "Neural Networks", 
               "Machine Learning", 
               "Algorithms",
               "Testing",
               "Mathematics",
               "Optimization",
               "Experimentation",
               "Statistics",
               "NLP",
               "Data",
               "Data Engineering",
               "Data Science",
              },
    "Data":   {"Data",
               "Data Engineering",
               "Data Science",
               "AWS",
               "SQL",
               "MongoDB",
               "MySQL",
               "JDBC",
               "Neo4J",
               "Apache TinkerPop",
               "AWS Neptune",
              },
    "Code":   {"Python",
    	       "Algorithms",
               "Software Engineering",
               "Implementation",
               "Linux","Bash",
               "Optimization",
               "OOP",
               "Java",
               "C++",
              },
    "Admin":  {"Docker","Kubernets",
               "Infrastructure",
               "Testing",
               "Linux","Bash",
               "Service Management",
               "SDLC",
               "AWS",
               "Network Administration",
               "CI/CD",
               "Git",
               "Integration",
              },
    "Bio":    {"Bioinformatics"},
    "Project":{"Collaboration",
               "Communication",
               "Project Management",
               "Product Requirements",
               "Service Management",
               "Value Creation",
               "SDLC",
               "Business Requirements",
              },
    "Soft":   {"Curious",
               "Teamwork",
               "Motivated",
               "Leadership",
               "Collaboration",
               "Ownership",
               "Communication Skills",
               "Innovation",
              },
    "Writing":{"Technical Communication",
               "Documentation",
               "Communication",
              },
    "Visual": {"Graphic Design"},
    "WebDev": {"Web Development",
               "React",
               "Flask",
              },
    "Java":   {"JDBC",
               "Java",
               "JavaFX",
              },
}

import hashlib, urllib

@dataclass(kw_only=True)
class JobListing:
    name:str
    skills_ranking:dict[str] = field(default_factory=dict)
    exports:list[str] = field(default_factory=list)
    stylesheet:str = "lighttheme"
    jinja2_render_args:dict = field(default_factory=dict)

    @classmethod
    def FromCats(cls, exports=None, debug=False, **kwargs):
        if exports is not None:
            skills_ranking = {Skill._clean_name(skill): weight for c_category, weight in exports.items() for skill in categories[c_category]}

            if debug:
                print(f"\n{kwargs} FromCats constructing a skills_ranking: {skills_ranking}")
            return cls(skills_ranking=skills_ranking, exports=[key for key, value in exports.items() if value], **kwargs)
        else:
            return cls(**kwargs)


    def export(self, resume:Resume, **kwargs):
        # Write the HTML-based hosted resume
        
    
        # name = urllib.parse.quote(self.name)
        if self.name == "index":
            public_name = self.name
            private_name = self.name

            public_path = f"resumes/{public_name}"
            private_path= f"pdf_sources/{private_name}"
        else:
            public_name = hashlib.md5(self.name.encode()).hexdigest()
            private_name = self.name

            public_path = f"resumes/{public_name}"
            private_path= f"pdf_sources/{private_name}/Zach_Allen_Resume"

            os.makedirs(f"docs/pdf_sources/{private_name}", exist_ok=True)

        

        urlsafe_private_path = urllib.parse.quote(private_path)
        
        resume.write_html_to_file(
            filepath=f"docs/{public_path}.html",
            jinja2_render_args = {
                "exports": self.exports,
                "stylesheet":self.stylesheet,
                **self.jinja2_render_args
            },
            popularity_dict = self.skills_ranking,
            suppress_popularity_threshold=(1, 0, ""),
            **kwargs
        )

        # Write the to-be-a-pdf resume
        
        resume.write_html_to_file(
            filepath=f"docs/{private_path}.html",
            alt_template_prefixes = {"*": "pdf"},
            jinja2_render_args = {
                "exports": self.exports,
                "resume_link": f"http://fractalmachini.st/{public_path}.html",
                "stylesheet":self.stylesheet,
                **self.jinja2_render_args
            },
            popularity_dict = self.skills_ranking,
            suppress_popularity_threshold=(1, 0, ""),
            **kwargs
        )

        return urlsafe_private_path

