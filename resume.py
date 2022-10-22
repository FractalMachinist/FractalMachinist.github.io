from CurriculumVitae import *
from datetime import date

sidebar_chars_per_line = 35.0

my_resume = Resume(
    person=Person(
        name="Zach Allen", pronouns="He/Him", 
        contact_info=ContactInfo(
            email="fractalmachinist@gmail.com", 
            phone="+1 (509)438-8146", 
            link="https://fractalmachini.st",
            link2="https://linkedin.com/in/zachallen-fractalmachinist/"
        )
    ),

    headline=' '.join(["Machine Learning Researcher & Data Engineer with 5 years experience in collaborative AI innovation & infrastructure implementation at scale.",                       
                       "Expert in Python & TensorFlow since 2015/2017.",
                       # "Analyzed, tested, and optimized innovative Machine Learning algorithms for unbalanced datasets (>1000:1), raising rare-case recognition from 15% to 90% with no loss in accuracy.",
                       "Passionate about working closely with multidisciplinary partners to shape the future towards global sustainability.",
                       # "Independently implemented and deployed terabyte-scale AWS genomics pipeline infrastructure in 4 months part-time, from no prior AWS or genomics experience.",
                       # "Certified in data-driven integrations of business needs, software engineering, project management, and software development best practices.",
                       "Excellent writing, speaking, presenting, and technical communication skills.",
                       ])
)

my_resume.education = [Occupation(
    must_render=True,
    title="Bachelor's in Computer Science", location="Utah, USA (Online)",
    timespan=Between(start=date(2019, 2, 1), end=date(2022, 8, 31)),
    subtitle="Western Governors University", 
    headline="Focused on Machine Learning and Project Management in a fully remote environment",
    skills=my_resume.Skills("Remote Work", "Project Management", "Machine Learning", "Computer Science", "Software Engineering"),
    sub_tasks=[
        Effort(
            title="Diamond Price Prediction Model",
            headline="End-to-End ML Model development and documentation for a mock gemstone marketplace",
            website="https://github.com/FractalMachinist/WGU-C968",
            skills=my_resume.Skills("Machine Learning", "End to End", "Documentation"),
            achievements=[
                Achievement(
                    headline="Researched & analyzed opportunities to integrate Machine Learning with existing infrasructure, merging technical requirements and business needs.",
                    skills=my_resume.Skills("Research", "Analysis", "Integration", "Infrastructure", "Managing Requirements")
                ),
                Achievement(
                    headline="Wrote & delivered project proposals, documentation, and performance reports, following best practices for technical and professional communication.",
                    skills=my_resume.Skills("Stakeholder Support", "Communication Skills", "Documentation", "Technical Communication", "Organizational Skills", "Best Practices")
                ),
                Achievement(
                    headline="Rapidly prototyped Python data pipeline in Numpy/Pandas and ML model in SciPy, demonstrating project validity quickly at least expense.",
                    skills=my_resume.Skills("Prototyping", "Python", "Data", "Numpy", "Pandas", "Machine Learning", "SciPy")
                ),
                Achievement(
                    headline="Integrated report generation and documentation in a Jupyter Notebook, providing Seaborn data visualization and embedded interactivity.",
                    skills=my_resume.Skills("Jupyter", "Seaborn", "Data Visualization")
                ),
            ]
        ), 
        Effort(
            title="Advanced Java Concepts",
            headline="Developed appointment scheduling and customer database tool in Java",
            website="https://github.com/FractalMachinist/C195-Scheduling-App",
            # skills=my_resume.Skills("Java", "Software Engineering", "Git", "SQL", "MySQL"),
            skills=my_resume.Skills("Java", "Software Engineering"),
            achievements=[
                Achievement(
                    # headline="Encapsulated Observable state and MySQL database connection state into a shared wrapper class, streamlining inheritance, error handling, and UI/Database auto-updates.",
                    headline="Streamlined Model-View coupling by encapsulating MySQL/JDBC connection objects with data processing steps and Observable outputs in a shared wrapper class.",
                    skills=my_resume.Skills("Java", "JavaFX", "JDBC", "SQL", "MySQL", "OOP")
                ),
                Achievement(
                    headline="Paid technical debt by finalizing project documentation.",
                    skills=my_resume.Skills("Documentation")
                )
            ]
        ),    
    ],
    
    achievements=[
        
        Certification(
            name="CompTIA Project+",
            headline="Demonstrated understanding of Project Management roles, processes, and documentation. Includes training in Agile.",
            issuer="Pearson VUE", issue_date=date(2019, 7, 24),
            website="https://wsr.pearsonvue.com/testtaker/authenticate/AuthenticateScoreReport.htm",
            confirmation_info={"Registration":"358639011", "Validation":"155946649"},
            skills=my_resume.Skills("Project Management", "Managing Requirements", "SDLC", "Agile", "Scope", "Stakeholder Support")
        ),
        
        Certification(
            name="IT Information Library Foundations Certification (ITIL)", 
            headline="Demonstrated understanding of designing, deploying, maintaining, and retiring IT resources to support business needs.",
            issuer="AXELOS", issue_date=date(2020, 8, 1),
            skills=my_resume.Skills("Infrastructure", "Managing Requirements")
        ),
        
        Certification(
            name="Site Development Associate",
            headline="Demonstrated ability to design and build websites.",
            issuer="CIW", issue_date=date(2019, 2, 1),
            skills=my_resume.Skills("Web Development", "HTML", "CSS", "JavaScript",)
        ),
        
        Achievement(
            headline="Excellence Award for Communication Applications",
            portfolio_link="https://github.com/FractalMachinist/Rust_Business_Presentation",
            skills=my_resume.Skills("Communication Skills", "Technical Communication")
        ),
])]

my_resume.employment = [
    Occupation(
        title="Sofware Engineer", location="St. Louis, Missouri, USA", website="https://PlutonBio.com",
        timespan=Between(start=date(2021, 3, 1), end=date(2021, 8, 31)),
        subtitle="Pluton Biosciences", supervisor=Person(name="Dr. Boahemaa Adu-Oppong", pronouns="She/Her",
                                                                contact_info=ContactInfo(email="BAdu-Oppong@plutonbio.com")),
        headline="Data Engineering and Cloud Infrastructure supporting Bioinformatics & Genomics research",
        skills=my_resume.Skills("Data", "Big Data", "Data Architecture", "Data Infrastructure", "Cloud Computing", "Bioinformatics", "Genomics", "Multidisciplinary", "Research"),
        sub_tasks=[
            Effort(
                title="AWS Genomics Pipeline",
                # headline="Independently designed, implemented, and deployed Terabyte-scale AWS genomics pipeline in 4 months part time, from no prior genomics or AWS experience.",
                headline="Terabyte-scale AWS genomics pipeline to meet rapidly growing startup needs",
                
                # skills=my_resume.Skills("AWS", "Cloud Computing", "Data", "Big Data", "Large Scale", "Infrastructure", "End to End", "Motivated", 
                #     "Multidisciplinary", "Problem Solving", "Remote Work", "Innovation", "Curious", "Ownership", "Project Management", "SDLC", "Data Architecture", "Data Infrastructure"),
                skills=my_resume.Skills("AWS", "Cloud Computing", "Data", "Big Data", "Large Scale", "Infrastructure", "Managing Requirements"),
                achievements=[
                    Achievement(
                        # title="Pipeline Design",
                        # headline="Designed, implemented, and documented gRPC+ProtoBuf pipeline architecture.",
                        # headline="Supported large scale data architecture needs and complex LIMS/metadata management with an in-house gRPC+ProtoBuf pipeline framework, ensuring strong integration between pipeline tools.",
                        headline="Ensured strong integration between pipeline components with an in-house gRPC+ProtoBuf pipeline architecture, built for LIMS/metadata integration from the ground-up.",
                        skills=my_resume.Skills("Large Scale", "Data", "Data Architecture", "Big Data", "Data Infrastructure", "Frameworks", "Integration", "Tooling")
                        # skills=my_resume.Skills("Infrastructure", "Data", "Big Data", "Large Scale", "Tooling", "Integration", "Automation", "Prototyping", "Workflows", "Innovation", "Problem Solving"),
                    ),
                    Achievement(
                        # title="User-Friendly Query Library",
                        # headline="Designed, implemented, developed training for, and documented an in-house Python+R library and interface enabling (non-CS) biologists to easily deploy multi-stage genomics queries without relying on the CS team.",
                        # headline="Accelerated research iteration with a tailor-made Python+R interface, helping non-CS teammates deploy complex multi-stage genomics analysis queries without relying on the CS team.",
                        # headline="Demonstrated experience in operational problem-solving with a custom Python+R framework, enabling non-CS teammates to deploy large-scale genomic analysis queries independent of the bottlenecked CS team.",
                        headline="Demonstrated experience using CS to meet business needs: Developed simple Python+R framework enabling non-CS teammates to deploy large-scale genomic analysis queries, without 'blocking on' the bottlenecked CS team.",
                        # headline="Integrated problem-solving experience with Computer Science knowledge: Identified an operational bottleneck where the Biology team polled the CS team to manually submit queries to the (then-prototype) data pipeline; "+
                        #          "Utilized Python and R to develop a simple 'non-blocking' interface, enabling Bio teammates to submit prototype pipeline queries without waiting on the CS team; "+
                        #          "Diverting time away from pipeline development towards a prototype interface freed up developer time and accelerated Bio R&D iteration, helping meet business needs.",
                        skills=my_resume.Skills("Integration", "Problem Solving", "Experience", "Computer Science", "Knowledge", "Python", "R", "Optimization")
                        # skills=my_resume.Skills("Python", "R", "API Design", "Libraries", "Tooling", "Automation", "Workflows", "Problem Solving", "Stakeholder Support") # Innovation?
                    ),
                    Achievement(
                        # title="Aligned Deliverables with Stakeholder Needs",
                        # headline="Collaborated with SMEs to gather, interpret, and meet data pipeline requirements, ensuring rapid value delivery to support startup launch. Interfaced with Bioinformatics expert for genomics tool selection.",
                        headline="Ensured rapid deployment in a fast-paced startup by collaborating directly with multidisciplinary SMEs and stakeholders to gather and interpret data pipeline requirements. Communicated with Bioinformatics expert for genomics tool selection.",
                        skills=my_resume.Skills("Collaboration", "Multidisciplinary", "Communication Skills", "Stakeholder Support", "Technical Communication", "Managing Requirements")
                        # skills=my_resume.Skills("Managing Requirements", "Communication Skills", "Project Management", "Collaboration", "Multidisciplinary", "Scope", "Stakeholder Support", "Technical Communication")
                    ),
               ],
            ),
                       
            Effort(
                title="Containerized Deployment & Autoscaling",
                headline="Researched, containerized, documented, and deployed 10+ Computational Genomics tools to AWS ECS and EC2",
                skills=my_resume.Skills("Research", "Containerization", "Documentation", "Data Infrastructure", "AWS", "ECS", "EC2"),
                achievements=[
                    Achievement(
                        # title="Streamlined Pipeline Development Lifecycle",
                        # headline="Developed, documented, and utilized frameworks for automating Computational Genomics tool containerization.",
                        headline="Leveraged experience in Docker and Kubernetes to streamline & automate containerization workflow for Computational Genomics tools, turning user requests into production tools in as little as 6h.",
                        skills=my_resume.Skills("Experience", "Automation", "Containerization", "Workflows", "Genomics", "Tooling")
                        # skills=my_resume.Skills("Infrastructure", "Tooling", "SDLC", "Automation", "Workflows", "Problem Solving", "Docker", "Containerization")
                    ),
                    Achievement(
                        headline="Detected, diagnosed, and resolved compute resource inefficiencies. Ensured ECS and EC2 autoscaling optimized cluster efficiency and responsiveness.",
                        skills=my_resume.Skills("Debugging", "Monitoring", "Tracking", "Reporting", "ECS", "EC2", "AWS", "Cloud Computing")
                        # skills=my_resume.Skills("Optimization", "Debugging", "Iteration", "Monitoring", "Tracking", "Reporting", "ECS", "EC2")
                    ),
                ]
            ),    
                   
            Achievement(
                # title="Spearheaded SDLC & CI/CD",
                headline="Led the CS team in adopting SDLC tools like Git, AWS CodeCommit, and Docker / AWS Elastic Container Registry. Championed utilization of Microsoft Teams Kanban tools for project&process management.",
                skills=my_resume.Skills("Leadership", "SDLC", "Git", "Containerization", "Project Management", "Teamwork", "Workflows", "CI/CD", "Organizational Skills")
            ),
            Achievement(
                # title="Microbial Taxonomy Visualizations in R",
                headline="Worked closely with SMEs to perform statistical analysis and visualization of microbial taxonomy data in R.",
                skills=my_resume.Skills("Collaboration", "R", "Analysis", "Statistics", "Multidisciplinary", "Teamwork", "Data Visualization", "Technical Communication")
                # skills=my_resume.Skills("R", "Analysis", "Statistics", "Communication Skills", "Collaboration", "Multidisciplinary", "Teamwork", "Iteration", "Data Visualization", "Technical Communication")
            ),
        ],
    ),
    
    Occupation(
        title="Embedded Systems Engineer", location="Allentown, Pennsylvania, USA", website="https://AppliedSeparations.com",
        timespan=Between(start=date(2019, 1, 1), end=date(2020, 1, 25)),
        subtitle="Applied Separations", 
        supervisor=Person(
            name="Aaron Allen", 
            pronouns="He/Him", 
            contact_info=ContactInfo(email="mnrnln@gmail.com")
        ),
        
        headline="Custom C++ / Arduino pump control software for chromatography and analytical chemistry systems in C and C++",
        skills=my_resume.Skills("C", "C++", "Microcontrollers", "Multidisciplinary", "Computer Science"),
        # skills=my_resume.Skills("C", "C++", "Computer Science", "Microcontrollers", "Algorithms", "Software Engineering", "SDLC", "Mult),
        achievements=[
           Achievement(
               # headline="Wrote a simple heuristic scheduler & virtual threading to manage real-time (60Hz+) pump control, touch screen input, and data/control communication, all on a single Arduino Mega.",
               headline="Demonstrated knowledge of Computer Engineering to optimize hardware efficiency by developing simple heuristic scheduling algorithms & virtual threading to manage real-time (60Hz+) pump control, touch screen input, and data/control communication, all on a single Arduino Mega.",
               skills=my_resume.Skills("Knowledge", "Computer Engineering", "Optimization", "Statistics", "Algorithms", "Microcontrollers")
               # skills=my_resume.Skills("Algorithms", "Optimization", "Software Engineering", "Statistics", "Computer Science", "Microcontrollers", "Computer Engineering")
           ),

           Achievement(
               # headline="Designed and validated delivery prediction and smoothing algorithms for nonlinear feedback delay.",
               headline="Analyzed and validated stable delivery with a custom, high-performance smoothing algorithm for variable feedback delay.",
               skills=my_resume.Skills("Algorithms", "Computer Science", "Analysis", "Testing")
               # skills=my_resume.Skills("Algorithms", "Algebra", "Testing", "Computer Science", "Prototyping", "Analysis")
           )
        ]
    ),
              
    Occupation(
        title="Service Writer", location="Richland, Washington, USA", website="https://AlphaComputerCenter.com",
        cost=6, # I really don't expect to see this unless I see everything
        timespan=Between(start=date(2017, 12, 1), end=date(2018, 11, 30)),
        subtitle="Alpha Computer Center", 
        supervisor=Person(
            name="Frank Ward Jr.", 
            pronouns="He/Him",
            contact_info=ContactInfo(email="frankjr@alphacomputercenter.com",phone="+1 (509)946-4230")
        ),
        
        headline="Customer service, sales, and technician support",
        skills=my_resume.Skills("Communication Skills", "Linux"),
        achievements=[
            Achievement(
                headline="Ensured customers were able to accurately understand and communicate with repair technicians, improving customer service and reducing diagnostic time.",
                skills=my_resume.Skills("Communication Skills")
            ),
            
            Achievement(
                headline="Leveraged extensive Linux experience to rapidly identify and repair issues that couldn't be fixed by Mac diagnostic tools.",
                skills=my_resume.Skills("Linux", "Bash")
            ),
            
            Achievement(
                headline="Reduced call frequency with an informative website. See it on <a href='https://web.archive.org/web/20180113192132/http://www.alphacomputercenter.com/wordpress1/'>web archive</a>.",
                skills=my_resume.Skills("Web Development", "HTML", "CSS", "JavaScript")
            )
        ]
    ),
              
    Occupation(
        title="Machine Learning Researcher", location="Richland, Washington, USA", website="https://pnnl.gov",
        timespan=Between(start=date(2017, 1, 1), end=date(2017, 5, 31)),
        subtitle="Pacific Northwest National Laboratory", 
        supervisor=Person(
            name="Dr. Enoch Yeung", 
            pronouns="He/Him", 
            contact_info=ContactInfo(email="eyeung@ucsb.edu")
        ),
        
        headline="ML Research and Data Engineering - Research Internship",
        skills=my_resume.Skills("TensorFlow", "Python", "Machine Learning", "Deep Learning", "Neural Network Architectures", "Research", "Computer Science", "Analysis", "Statistics", "Software Engineering"),
        achievements=[
            Achievement(
                headline="Researched, Designed and tested novel ML & Neural Network algorithms, architectures, and error formulations for NLP, image classification, and time-series data classification.",
                skills=my_resume.Skills("Research", "Testing", "Machine Learning", "Neural Networks", "Algorithms", "Natural Language Processing", "Analysis", "Statistics")
                # skills=my_resume.Skills("Python", "TensorFlow", "Machine Learning", "Deep Learning", "Neural Network Architectures", "Feature Engineering",
                #                                 "Algorithms", "Algebra", "NLP", "Data", "Curious", "Research", "Frameworks", "Computer Science",
                #                                 "MatLab", "NumPy", "Software Engineering")
            ),
            
            Achievement(
                headline="Demonstrated increased test accuracy (15% ⇾ 90% detection with higher Bayesian Confidence) on unbalanced (>1000:1) datasets for network insider threat detection, without duplication, augmentation, or batch filtering.",
                skills=my_resume.Skills("Machine Learning", "Algebra", "Statistics", "Testing", "Research", "Algorithms", "Computer Science", "Analysis", "Software Engineering")
            ),
            
            Achievement(
                headline="Worked independently, balancing multiple projects and deliverables with minimal mentor supervision.",
                skills=my_resume.Skills("Project Management", "Reporting", "Ownership")
            )
        ]
    )
]



my_resume.projects = [
    Effort(
        title="Neural Cellular Segmentation",
        headline="Exploring neural cellular automata and attention (NCA+A) for medical image segmentation in TensorFlow",
        website="https://github.com/FractalMachinist/NeuralCellularAutomataAttn",
        skills=my_resume.Skills("Software Engineering", "Python", "TensorFlow", "Machine Learning", "Research", "Analysis", "Statistics", "Neural Network Architectures"),
        achievements=[
            Achievement(
                headline="Developed, tested, and iterated NCA+A models in TensorFlow, balancing system resources and model size.",
                chars_per_line=sidebar_chars_per_line, # Due to the sidebar. This needs refactored.
                skills=my_resume.Skills("Python", "TensorFlow", "Machine Learning", "Neural Network Architectures", "Research", "Algebra", 
                                                "Optimization", "Statistics", "NumPy", "Analysis")
            ),
            Achievement(
                headline="Created multiple tf.Data pipelines with preprocessing and data augmentation steps.",
                chars_per_line=sidebar_chars_per_line, # Due to the sidebar. This needs refactored.
                skills=my_resume.Skills("Python", "Data", "Software Engineering", "TensorFlow", "Git", "Frameworks", "Computer Science")
            ),
        ]
    ),
    Effort(
        title="Interplan",
        headline="Task dependency management from a Graph Database",
        website="https://github.com/FractalMachinist/Interplan",
        skills=my_resume.Skills("Software Engineering", "Neo4J", "Web Development", "Containerization", "Project Management"),
        achievements=[
            Achievement(
                headline="Developed a Neo4J+JS dependency resolution and task status tracking API.",
                chars_per_line=sidebar_chars_per_line, # Due to the sidebar. This needs refactored.
                skills=my_resume.Skills("Data", "JavaScript", "Testing", "Project Management", "Data Driven", "API Design",
                                                   "Software Engineering", "Neo4J", "Apache Tinkerpop")
            ),

            Achievement(
                headline="Designed intuitive React app for displaying and interacting with tasks.",
                chars_per_line=sidebar_chars_per_line, # Due to the sidebar. This needs refactored.
                skills=my_resume.Skills("Web Development", "HTML", "CSS", "JavaScript", "React")
            ),

            Achievement(
                headline="Packaged Node+Neo4J in Docker & Kubernetes for easy migration.",
                chars_per_line=sidebar_chars_per_line, # Due to the sidebar. This needs refactored.
                skills=my_resume.Skills("Containerization", "Infrastructure")
            )
        ]
    ),
    
    Effort(
        title="MarkNotes",
        headline="Intuitive journaling tool designed to encourage long-term review and introspection",
        website="https://github.com/FractalMachinist/MarkNotes",
        skills=my_resume.Skills("Software Engineering", "Web Development", "NoSQL", "MongoDB"),
        achievements=[
            Achievement(
                headline="Integrated MongoDB and Node API for destructuring, storing, and querying Markdown entries as semi-structured data.",
                chars_per_line=sidebar_chars_per_line, # Due to the sidebar. This needs refactored.
                skills=my_resume.Skills("MongoDB", "Data", "Data Driven", "NoSQL", "API Design")
            ),

            Achievement(
                headline="Designed simple, intuitive React web app interface.",
                chars_per_line=sidebar_chars_per_line, # Due to the sidebar. This needs refactored.
                skills=my_resume.Skills("Web Development", "HTML", "CSS", "JavaScript")
            ),

            Achievement(
                headline="Packaged Node+MongoDB in Docker & Kubernetes.",
                chars_per_line=sidebar_chars_per_line, # Due to the sidebar. This needs refactored.
                skills=my_resume.Skills("Containerization", "Infrastructure")
            )
        ]
    ),
    
    Effort(
        title="NetTimeLog",
        headline="Minimalist, accurate time tracking",
        # website="https://fractalmachini.st/demos/nettimelog",
        achievements=[
            Achievement(
                headline="Created time-tracking web app with Python+Flask which records what you just completed, so you never estimate what you will do or how long it will take.",
                chars_per_line=sidebar_chars_per_line, # Due to the sidebar. This needs refactored.
                skills=my_resume.Skills("Web Development", "HTML", "CSS", "JavaScript")
            )
        ]
    )
]