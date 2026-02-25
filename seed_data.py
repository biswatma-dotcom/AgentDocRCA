import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.database import (
    init_db, get_db_context, create_project, create_requirement_set, update_requirement_set_bullets,
    create_block_template, create_new_version, create_change_log, get_block_templates, get_requirement_sets
)


def seed_data():
    init_db()
    
    with get_db_context() as db:
        existing_projects = db.execute("SELECT COUNT(*) FROM projects").fetchone()
        if existing_projects[0] > 0:
            print("Database already has data. Skipping seed.")
            return
        
        print("Seeding sample data...")
        
        project = create_project(
            name="Voice Assistant for Banking",
            client_name="ABC Bank"
        )
        print(f"Created project: {project.name}")
        
        req_set = create_requirement_set(
            project_id=str(project.id),
            title="Core Banking Requirements",
            raw_text="The voice agent must handle balance inquiries, transaction history, and fund transfers. It must support English and Spanish. It must comply with PCI-DSS for sensitive data. Response time must be under 3 seconds.",
            created_by="admin"
        )
        
        bullets = [
            "Handle balance inquiries",
            "Provide transaction history",
            "Process fund transfers",
            "Support English and Spanish",
            "Comply with PCI-DSS",
            "Respond within 3 seconds"
        ]
        update_requirement_set_bullets(str(req_set.id), bullets)
        print(f"Created requirement set: {req_set.title}")
        
        block1 = create_block_template(
            project_id=str(project.id),
            name="Persona",
            order_index=0,
            placeholder="Describe the voice agent's persona, tone, and characteristics..."
        )
        
        block2 = create_block_template(
            project_id=str(project.id),
            name="Flow",
            order_index=1,
            placeholder="Document the conversation flow, intents, and handling..."
        )
        
        block3 = create_block_template(
            project_id=str(project.id),
            name="FAQs",
            order_index=2,
            placeholder="List common questions and answers..."
        )
        
        print("Created block templates: Persona, Flow, FAQs")
        
        version1_content = {
            str(block1.id): "Professional and helpful banking assistant. Uses formal but friendly tone.",
            str(block2.id): "Main flow: greeting -> authentication -> main menu -> intent handling -> confirmation -> goodbye.",
            str(block3.id): "Q: What is my balance? A: I can help with that. Q: How do I transfer money? A: Here's how..."
        }
        
        version1 = create_new_version(
            project_id=str(project.id),
            blocks_content=version1_content,
            created_by="admin",
            change_summary="Initial version"
        )
        
        print(f"Created version {version1.version_number}")
        
        version2_content = {
            str(block1.id): "Professional and helpful banking assistant. Uses formal but friendly tone. Speaks clearly and slowly.",
            str(block2.id): "Main flow: greeting -> authentication -> main menu -> intent handling -> confirmation -> goodbye. Added escalation flow for complex issues.",
            str(block3.id): "Q: What is my balance? A: I can help with that. Q: How do I transfer money? A: Here's how... Q: What are your hours? A: We are available 24/7."
        }
        
        version2 = create_new_version(
            project_id=str(project.id),
            blocks_content=version2_content,
            created_by="admin",
            change_summary="Updated persona, added escalation flow, expanded FAQs"
        )
        
        create_change_log(
            doc_version_id=str(version2.id),
            template_block_id=str(block1.id),
            before_text="Professional and helpful banking assistant. Uses formal but friendly tone.",
            after_text="Professional and helpful banking assistant. Uses formal but friendly tone. Speaks clearly and slowly.",
            requirement_set_id=str(req_set.id),
            requirement_bullet_indexes=[0],
            reason_why="Improved clarity for elderly users",
            impact="low"
        )
        
        print(f"Created version {version2.version_number} with change log")
        
        print("\nSeed data created successfully!")
        print(f"Project ID: {project.id}")
        print("You can now run the app and select this project.")


if __name__ == "__main__":
    seed_data()
