from typing import Any

personal_data: dict[str, Any] = {
    "personal_info": {
        "name": "Kedar Damale",
        "location": "Thane, MH, India",
        "phone": "+91 7058533020",
        "email": "damalekedar@gmail.com",
        "links": [
            "Portfolio Website: https://kedardamale.github.io/KedarDamale",
            "GitHub: https://github.com/KedarDamale",
            "LinkedIn: https://www.linkedin.com/in/kedar-damale-57252a324",
        ],
    },
    "summary": "Applied Data Scientist with 1.5 years of experience building end-to-end AI/ML solutions across fintech, financial automation, pharma, and medical research. Experienced in machine learning, Generative AI, multi-agent systems, and data pipeline development, with a focus on translating research and experimentation into deployable, production-grade applications.",
    
    "skills": {
        "programming_and_data": [
            "Python",
            "SQL",
            "Pydantic",
            "Databricks",
            "DuckDB",
            "NumPy",
            "Pandas",
            "Polars",
        ],
        "machine_learning": [
            "NLP",
            "Scikit-learn",
            "XGBoost",
            "Feature Engineering",
            "Cross-Validation",
            "Model Evaluation",
            "Hyperparameter Tuning",
        ],
        "deep_learning": [
            "PyTorch",
            "YOLO",
            "Transfer Learning",
            "Model Training and Evaluation",
        ],
        "generative_ai": [
            "LangChain",
            "LangGraph",
            "RAG",
            "Multi-Agent Systems",
            "Tool Calling",
            "MCP",
            "Human-in-the-Loop (HITL)",
        ],
        "data_engineering_and_mlops": [
            "ETL/ELT Pipelines",
            "MLflow",
            "FastAPI",
            "Docker",
            "AWS",
            "CI/CD",
            "Git/GitHub",
        ],
        "mathematics_and_statistics": [
            "Probability and Statistics",
            "Hypothesis Testing",
            "Confidence Intervals",
            "Linear Algebra",
            "Calculus",
        ],
    },
    "work_experience": [
        {
            "title": "ML and GenAI Engineer",
            "company": "GlobalSpace Technologies Ltd.",
            "location": "Navi Mumbai, MH, India",
            "duration": "Jan 2026-Present",
            "projects_or_roles": [
                {
                    "name": "Budget Automation and Incentive Calculator",
                    "details": [
                        (
                            "Replaced a per-employee XGBoost modeling approach "
                            "with a unified, hierarchy-aware target allocation "
                            "system designed to scale from 20-30 employees to "
                            "thousands of MRs, under review by pharmaceutical "
                            "companies including Himalaya and Zydus."
                        ),
                        (
                            "Built a top-down budgeting workflow that allocates "
                            "targets based on historical performance and "
                            "capacity, supports time-bound revision requests, "
                            "reconciles conflicting requests, and routes "
                            "proposed changes for managerial approval."
                        ),
                        (
                            "Developed a DAG-based incentive calculation engine "
                            "with an AI agent that converts policy PDFs into "
                            "executable logic at runtime and explains "
                            "employee-level incentive outcomes, enabling "
                            "business users to update incentive policies "
                            "without specialist admin support."
                        ),
                    ],
                },
                {
                    "name": "PatGPT",
                    "details": [
                        (
                            "Rebuilt a pharmaceutical sales analytics platform "
                            "around an agentic architecture for multi-step "
                            "forecasting, simulation, prediction, and "
                            "historical analysis across 3M+ sales and tender "
                            "records."
                        ),
                        (
                            "Implemented human-in-the-loop review checkpoints "
                            "and evidence-grounded responses to support "
                            "verifiable, multi-step commercial analysis and "
                            "recommendations."
                        ),
                        (
                            "Added streamed responses, safe retry handling, and "
                            "checksum-verified data promotion and rollback; "
                            "platform is now used at Zydus."
                        ),
                    ],
                },
            ],
        },
        {
            "title": "Automation Developer",
            "company": "Propelligence Advisors Pvt. Ltd.",
            "location": "Thane, MH, India",
            "duration": "May 2025-Jan 2026",
            "details": [
                (
                    "Automated purchase-register to GSTR-2B invoice "
                    "reconciliation, addressing inconsistent vendor names, "
                    "invoice identifiers, and date formats that made "
                    "exact-match approaches unreliable."
                ),
                (
                    "Engineered a large-file reconciliation pipeline using "
                    "fuzzy matching, match threshold, date/value "
                    "tolerances, Polars processing, and constant-memory report "
                    "generation."
                ),
                (
                    "Processed 10,000+ invoice entries in 12 seconds versus "
                    "5-6 days manually, reducing processing time by over "
                    "99.996% with 100% precision and no false positives till "
                    "this date."
                ),
                (
                    "Integrated the module into an audit suite adopted by two "
                    "CA firms and approximately 20 auditors."
                ),
            ],
        },
    ],
    "projects": [
        {
            "name": "Chessablanka: Chess Position Analyzer",
            "link": "GitHub Link",
            "details": [
                (
                    "Built a computer-vision tool that converts chessboard "
                    "photos into playable positions, eliminating manual board "
                    "transcription for chess analysis and college competition "
                    "preparation."
                ),
                (
                    "Trained a custom YOLOv8 model using an augmented dataset "
                    "of 1,700+ images to detect chess pieces and reconstruct "
                    "board positions from photos."
                ),
                (
                    "Achieved 98.57% detection accuracy across 500+ test "
                    "images and integrated Stockfish for position evaluation "
                    "and best-move recommendations; used by the college IT "
                    "chess team for competition preparation."
                ),
            ],
        },
        {
            "name": "NeuroTRIBE: Brain Activity Analysis for ADHD Research",
            "link": "GitHub Link",
            "details": [
                (
                    "Developed a neuroimaging research pipeline to investigate "
                    "differences in brain responses to movie stimuli between "
                    "participants with and without ADHD."
                ),
                (
                    "Automated the analysis of fMRI data using pretrained "
                    "brain-activity models to identify patterns across brain "
                    "regions and networks."
                ),
                (
                    "Applied statistical testing with confounding-factor "
                    "adjustments and generated 3D brain visualizations and "
                    "reports to support research analysis."
                ),
            ],
        },
        {
            "name": "CattleMO: Low-Cost Cattle Monitoring with ESP32 and DBSCAN",
            "link": "GitHub Link",
            "details": [
                (
                    "Designed a low-cost cattle monitoring system that reduces "
                    "dependence on individual GPS trackers by estimating "
                    "animal proximity through wireless signal strength."
                ),
                (
                    "Led development of an ESP32-based tracking prototype with "
                    "a GPS-equipped master node, wireless child nodes, and a "
                    "live dashboard for monitoring herd movement."
                ),
                (
                    "Applied DBSCAN clustering to identify grazing zones and "
                    "movement patterns, with telemetry processed through "
                    "Flask and MongoDB and displayed in a Next.js dashboard."
                ),
            ],
        },
    ],
    "education_and_achievements": [
        (
            "Qualified GATE DA 2026 and graduated in IT Engineering with an "
            "8.5 CGPA from Mumbai University."
        ),
        (
            "Published an automation suite for CA and audit firms, adopted by "
            "two CA firms and used by approximately 20 auditors."
        ),
    ],
}
