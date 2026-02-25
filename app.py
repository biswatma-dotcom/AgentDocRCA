import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from modules.database import (
    init_db, get_db_session, get_projects, get_project, create_project,
    get_requirement_sets, get_requirement_set, create_requirement_set, update_requirement_set_bullets,
    get_block_templates, create_block_template, update_block_template, delete_block_template,
    get_latest_version, get_version, get_all_versions, create_new_version, get_change_logs_for_version, create_change_log
)
from modules.openai_helper import normalize_requirements
from modules.docx_generator import generate_docx_bytes
from modules.pdf_generator import generate_pdf_bytes

load_dotenv()

APP_PASSWORD = os.getenv('APP_PASSWORD', 'admin')


def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'selected_project_id' not in st.session_state:
        st.session_state.selected_project_id = None
    if 'editor_content' not in st.session_state:
        st.session_state.editor_content = {}
    if 'change_mapping' not in st.session_state:
        st.session_state.change_mapping = {}
    if 'show_change_mapping' not in st.session_state:
        st.session_state.show_change_mapping = False


def check_password():
    if not APP_PASSWORD:
        st.session_state.logged_in = True
        return True
    
    if 'password_attempted' not in st.session_state:
        st.session_state.password_attempted = False
    
    st.title("AgentDocRCA - Login")
    
    password = st.text_input("Enter Password", type="password")
    
    if st.button("Login"):
        if password == APP_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.password_attempted = True
            st.rerun()
        else:
            st.error("Incorrect password")
            st.session_state.password_attempted = True
    
    return False


def sidebar_nav():
    st.sidebar.title("Navigation")
    pages = ["Projects", "Requirements", "Block Settings", "Editor", "Versions"]
    selected = st.sidebar.radio("Go to", pages)
    
    if 'nav_selection' not in st.session_state or st.session_state.nav_selection != selected:
        st.session_state.nav_selection = selected
    
    st.sidebar.markdown("---")
    
    db = get_db_session()
    try:
        projects = list(get_projects(db))
    finally:
        db.close()
    
    project_options = ["-- Select Project --"] + [p.name for p in projects]
    
    if projects:
        selected_idx = 0
        if st.session_state.selected_project_id:
            for i, p in enumerate(projects):
                if str(p.id) == str(st.session_state.selected_project_id):
                    selected_idx = i + 1
                    break
        
        selected_name = st.sidebar.selectbox(
            "Select Project",
            project_options,
            index=selected_idx,
            key="project_selector"
        )
        
        if selected_name != "-- Select Project --":
            selected_project = next((p for p in projects if p.name == selected_name), None)
            if selected_project:
                st.session_state.selected_project_id = str(selected_project.id)
        else:
            st.session_state.selected_project_id = None
    
    return st.session_state.nav_selection


def page_projects():
    st.header("Projects")
    
    with st.expander("Create New Project", expanded=False):
        with st.form("create_project_form"):
            name = st.text_input("Project Name")
            client_name = st.text_input("Client Name")
            submitted = st.form_submit_button("Create Project")
            
            if submitted and name:
                db = get_db_session()
                try:
                    create_project(db, name=name, client_name=client_name)
                finally:
                    db.close()
                st.success(f"Project '{name}' created!")
                st.rerun()
    
    st.subheader("All Projects")
    db = get_db_session()
    try:
        projects = get_projects(db)
    finally:
        db.close()
    
    if not projects:
        st.info("No projects yet. Create one to get started.")
        return
    
    for p in projects:
        with st.expander(f"{p.name} ({p.client_name or 'No client'})"):
            st.write(f"**Created:** {p.created_at.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**ID:** {p.id}")


def page_requirements():
    st.header("Requirements")
    
    if not st.session_state.selected_project_id:
        st.warning("Please select a project from the sidebar.")
        return
    
    db = get_db_session()
    try:
        project = get_project(db, st.session_state.selected_project_id)
    finally:
        db.close()
    
    st.subheader(f"Requirements for: {project.name}")
    
    with st.expander("Add New Requirement Set", expanded=False):
        with st.form("create_requirement_form"):
            title = st.text_input("Requirement Title")
            raw_text = st.text_area("Raw Requirements Text", height=150)
            submitted = st.form_submit_button("Create Requirement Set")
            
            if submitted and title:
                db = get_db_session()
                try:
                    create_requirement_set(
                        db,
                        project_id=st.session_state.selected_project_id,
                        title=title,
                        raw_text=raw_text,
                        created_by="user"
                    )
                finally:
                    db.close()
                st.success(f"Requirement set '{title}' created!")
                st.rerun()
    
    st.subheader("Existing Requirement Sets")
    db = get_db_session()
    try:
        req_sets = get_requirement_sets(db, st.session_state.selected_project_id)
    finally:
        db.close()
    
    if not req_sets:
        st.info("No requirement sets yet.")
        return
    
    for rs in req_sets:
        with st.expander(f"{rs.title}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if rs.raw_text:
                    st.write("**Raw Text:**")
                    st.text(rs.raw_text, help=None)
            
            with col2:
                st.write("**Normalized Bullets:**")
                if rs.normalized_bullets:
                    for i, bullet in enumerate(rs.normalized_bullets):
                        st.write(f"{i+1}. {bullet}")
                else:
                    st.info("Not normalized")
            
            if st.button(f"Normalize: {rs.id}", key=f"normalize_{rs.id}"):
                if rs.raw_text:
                    with st.spinner("Normalizing with AI..."):
                        bullets = normalize_requirements(rs.raw_text)
                        if bullets:
                            db = get_db_session()
                            try:
                                update_requirement_set_bullets(db, str(rs.id), bullets)
                            finally:
                                db.close()
                            st.success(f"Normalized to {len(bullets)} bullets!")
                            st.rerun()
                        else:
                            st.error("Failed to normalize. Check OpenAI API key.")
                else:
                    st.warning("No raw text to normalize")


def page_block_settings():
    st.header("Block Settings")
    
    if not st.session_state.selected_project_id:
        st.warning("Please select a project from the sidebar.")
        return
    
    db = get_db_session()
    try:
        project = get_project(db, st.session_state.selected_project_id)
    finally:
        db.close()
    
    st.subheader(f"Block Templates for: {project.name}")
    
    db = get_db_session()
    try:
        blocks = get_block_templates(db, st.session_state.selected_project_id)
    finally:
        db.close()
    
    with st.expander("Add New Block", expanded=False):
        with st.form("add_block_form"):
            name = st.text_input("Block Name")
            placeholder = st.text_area("Placeholder Text", height=100)
            submitted = st.form_submit_button("Add Block")
            
            if submitted and name:
                db = get_db_session()
                try:
                    create_block_template(
                        db,
                        project_id=st.session_state.selected_project_id,
                        name=name,
                        order_index=len(blocks) if blocks else 0,
                        placeholder=placeholder
                    )
                finally:
                    db.close()
                st.success(f"Block '{name}' added!")
                st.rerun()
    
    st.subheader("Existing Blocks")
    
    if not blocks:
        st.info("No blocks defined. Add one above.")
        return
    
    for i, block in enumerate(blocks):
        col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
        
        with col1:
            new_name = st.text_input(f"Name {block.id}", value=block.name, key=f"name_{block.id}")
        with col2:
            new_placeholder = st.text_area(f"Placeholder {block.id}", value=block.placeholder or "", height=50, key=f"placeholder_{block.id}")
        with col3:
            if st.button("Up", key=f"up_{block.id}") and i > 0:
                db = get_db_session()
                try:
                    update_block_template(db, str(block.id), order_index=i-1)
                    update_block_template(db, str(blocks[i-1].id), order_index=i)
                finally:
                    db.close()
                st.rerun()
        with col4:
            if st.button("Down", key=f"down_{block.id}") and i < len(blocks) - 1:
                db = get_db_session()
                try:
                    update_block_template(db, str(block.id), order_index=i+1)
                    update_block_template(db, str(blocks[i+1].id), order_index=i)
                finally:
                    db.close()
                st.rerun()
        
        col_save, col_del = st.columns([1, 1])
        with col_save:
            if st.button("Save", key=f"save_{block.id}"):
                db = get_db_session()
                try:
                    update_block_template(db, str(block.id), name=new_name, placeholder=new_placeholder)
                finally:
                    db.close()
                st.success("Saved!")
                st.rerun()
        with col_del:
            if st.button("Delete", key=f"del_{block.id}"):
                db = get_db_session()
                try:
                    delete_block_template(db, str(block.id))
                finally:
                    db.close()
                st.rerun()
        
        st.divider()


def page_editor():
    st.header("Editor")
    
    if not st.session_state.selected_project_id:
        st.warning("Please select a project from the sidebar.")
        return
    
    db = get_db_session()
    try:
        project = get_project(db, st.session_state.selected_project_id)
        blocks = get_block_templates(db, st.session_state.selected_project_id)
    finally:
        db.close()
    
    if not blocks:
        st.warning("No blocks defined. Go to Block Settings to add blocks.")
        return
    
    db = get_db_session()
    try:
        latest_version = get_latest_version(db, st.session_state.selected_project_id)
    finally:
        db.close()
    
    if latest_version:
        st.info(f"Latest version: {latest_version.version_number}")
    else:
        st.info("No versions yet. This will be Version 1.")
    
    st.subheader("Edit Document")
    
    if 'editor_initialized' not in st.session_state or st.session_state.get('last_project') != st.session_state.selected_project_id:
        st.session_state.editor_content = {}
        if latest_version and latest_version.blocks_content:
            st.session_state.editor_content = {str(k): v for k, v in latest_version.blocks_content.items()}
        st.session_state.editor_initialized = True
        st.session_state.last_project = st.session_state.selected_project_id
    
    current_content = {}
    
    for block in blocks:
        block_id = str(block.id)
        default_value = st.session_state.editor_content.get(block_id, block.placeholder or "")
        
        content = st.text_area(
            f"{block.name}",
            value=default_value,
            height=150,
            key=f"editor_{block_id}",
            placeholder=block.placeholder
        )
        current_content[block_id] = content
    
    if st.button("Check for Changes"):
        st.session_state.current_content = current_content
        
        db = get_db_session()
        try:
            latest_version = get_latest_version(db, st.session_state.selected_project_id)
        finally:
            db.close()
        
        if latest_version and latest_version.blocks_content:
            changed_blocks = []
            for block in blocks:
                block_id = str(block.id)
                old_content = latest_version.blocks_content.get(block_id, "")
                new_content = current_content.get(block_id, "")
                
                if old_content.strip() != new_content.strip():
                    changed_blocks.append({
                        'block_id': block_id,
                        'block_name': block.name,
                        'before': old_content,
                        'after': new_content
                    })
            
            if changed_blocks:
                st.session_state.changed_blocks = changed_blocks
                st.session_state.show_change_mapping = True
                st.rerun()
            else:
                st.warning("No changes detected!")
        else:
            changed_blocks = []
            for block in blocks:
                block_id = str(block.id)
                new_content = current_content.get(block_id, "")
                if new_content.strip():
                    changed_blocks.append({
                        'block_id': block_id,
                        'block_name': block.name,
                        'before': "",
                        'after': new_content
                    })
            
            if changed_blocks:
                st.session_state.changed_blocks = changed_blocks
                st.session_state.show_change_mapping = True
                st.rerun()
            else:
                st.warning("No content to save!")
    
    if st.session_state.get('show_change_mapping') and st.session_state.get('changed_blocks'):
        st.divider()
        st.subheader("Change Mapping Section")
        
        st.write("Map each changed block to requirements:")
        
        db = get_db_session()
        try:
            requirement_sets = get_requirement_sets(db, st.session_state.selected_project_id)
        finally:
            db.close()
        
        if not requirement_sets:
            st.error("No requirement sets available. Create one first.")
            st.session_state.show_change_mapping = False
            return
        
        all_filled = True
        
        for cb in st.session_state.changed_blocks:
            st.write(f"**Block: {cb['block_name']}**")
            
            key_prefix = f"mapping_{cb['block_id']}"
            
            if key_prefix not in st.session_state:
                st.session_state[key_prefix] = {
                    'requirement_set_id': None,
                    'bullet_indexes': [],
                    'reason_why': '',
                    'impact': 'low'
                }
            
            mapping = st.session_state[key_prefix]
            
            req_options = {str(rs.id): rs.title for rs in requirement_sets}
            req_options_list = ["-- Select --"] + list(req_options.values())
            
            selected_req_title = st.selectbox(
                f"Requirement Set for {cb['block_name']}",
                req_options_list,
                key=f"req_{key_prefix}"
            )
            
            if selected_req_title != "-- Select --":
                selected_req_id = [k for k, v in req_options.items() if v == selected_req_title][0]
                mapping['requirement_set_id'] = selected_req_id
                
                db = get_db_session()
                try:
                    req_set = get_requirement_set(db, selected_req_id)
                finally:
                    db.close()
                
                if req_set and req_set.normalized_bullets:
                    bullet_options = {i: f"{i+1}. {b}" for i, b in enumerate(req_set.normalized_bullets)}
                    selected_bullets = st.multiselect(
                        f"Select Bullet(s) for {cb['block_name']}",
                        options=list(bullet_options.keys()),
                        format_func=lambda x: bullet_options[x],
                        key=f"bullets_{key_prefix}"
                    )
                    mapping['bullet_indexes'] = [int(x) for x in selected_bullets]
                else:
                    st.warning("This requirement set has no normalized bullets")
            else:
                mapping['requirement_set_id'] = None
            
            mapping['reason_why'] = st.text_input(
                f"Reason Why (required)",
                value=mapping['reason_why'],
                key=f"reason_{key_prefix}"
            )
            
            mapping['impact'] = st.selectbox(
                f"Impact",
                ['low', 'med', 'high'],
                index=['low', 'med', 'high'].index(mapping['impact']),
                key=f"impact_{key_prefix}"
            )
            
            if not mapping['requirement_set_id'] or not mapping['reason_why']:
                all_filled = False
            
            st.divider()
        
        if st.button("Confirm & Save Version"):
            if all_filled:
                db = get_db_session()
                try:
                    new_version = create_new_version(
                        db,
                        project_id=st.session_state.selected_project_id,
                        blocks_content=st.session_state.current_content,
                        created_by="user"
                    )
                    
                    for cb in st.session_state.changed_blocks:
                        key_prefix = f"mapping_{cb['block_id']}"
                        mapping = st.session_state[key_prefix]
                        
                        create_change_log(
                            db,
                            doc_version_id=str(new_version.id),
                            template_block_id=cb['block_id'],
                            before_text=cb['before'],
                            after_text=cb['after'],
                            requirement_set_id=mapping['requirement_set_id'],
                            requirement_bullet_indexes=mapping['bullet_indexes'],
                            reason_why=mapping['reason_why'],
                            impact=mapping['impact']
                        )
                finally:
                    db.close()
                
                st.session_state.show_change_mapping = False
                st.session_state.changed_blocks = []
                st.session_state.editor_content = st.session_state.current_content
                st.success(f"Version {new_version.version_number} saved!")
                st.rerun()
            else:
                st.error("Please fill in all required fields (Requirement Set and Reason Why)")
        
        if st.button("Cancel"):
            st.session_state.show_change_mapping = False
            st.session_state.changed_blocks = []
            st.rerun()


def page_versions():
    st.header("Versions / RCA")
    
    if not st.session_state.selected_project_id:
        st.warning("Please select a project from the sidebar.")
        return
    
    db = get_db_session()
    try:
        project = get_project(db, st.session_state.selected_project_id)
        blocks = get_block_templates(db, st.session_state.selected_project_id)
        requirement_sets = get_requirement_sets(db, st.session_state.selected_project_id)
        versions = get_all_versions(db, st.session_state.selected_project_id)
    finally:
        db.close()
    
    if not versions:
        st.info("No versions yet.")
        return
    
    st.subheader(f"Version History for: {project.name}")
    
    for version in versions:
        with st.expander(f"Version {version.version_number} - {version.created_at.strftime('%Y-%m-%d %H:%M')}"):
            st.write(f"**Created:** {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Document Content")
                blocks_dict = version.blocks_content if version.blocks_content else {}
                
                for block in blocks:
                    st.write(f"**{block.name}:**")
                    content = blocks_dict.get(str(block.id), "")
                    if content:
                        st.text(content)
                    else:
                        st.text("[No content]")
            
            with col2:
                db = get_db_session()
                try:
                    change_logs = get_change_logs_for_version(db, str(version.id))
                finally:
                    db.close()
                
                if change_logs:
                    st.subheader("RCA - Change Log")
                    
                    for log in change_logs:
                        block = next((b for b in blocks if str(b.id) == str(log.template_block_id)), None)
                        req_set = next((rs for rs in requirement_sets if str(rs.id) == str(log.requirement_set_id)), None)
                        
                        st.write(f"**Block:** {block.name if block else 'Unknown'}")
                        st.write(f"**Requirement:** {req_set.title if req_set else 'Unknown'}")
                        
                        if log.requirement_bullet_indexes and req_set and req_set.normalized_bullets:
                            st.write("**Bullet(s):**")
                            for idx in log.requirement_bullet_indexes:
                                if idx < len(req_set.normalized_bullets):
                                    st.write(f"  - {req_set.normalized_bullets[idx]}")
                        
                        st.write(f"**Why:** {log.reason_why}")
                        st.write(f"**Impact:** {log.impact.upper()}")
                        st.divider()
                else:
                    st.info("No changes in this version (initial version)")
            
            st.subheader("Download")
            
            db = get_db_session()
            try:
                change_logs = get_change_logs_for_version(db, str(version.id))
            finally:
                db.close()
            
            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                docx_bytes = generate_docx_bytes(project, version, blocks, change_logs, requirement_sets, blocks)
                st.download_button(
                    label="Download DOCX",
                    data=docx_bytes,
                    file_name=f"{project.name}_v{version.version_number}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            
            with col_d2:
                pdf_bytes = generate_pdf_bytes(project, version, blocks, change_logs, requirement_sets, blocks)
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"{project.name}_v{version.version_number}.pdf",
                    mime="application/pdf"
                )


def main():
    st.set_page_config(
        page_title="AgentDocRCA",
        page_icon="📄",
        layout="wide"
    )
    
    init_session_state()
    
    if not st.session_state.logged_in:
        if check_password():
            pass
        else:
            return
    
    try:
        init_db()
    except ValueError as e:
        st.error(str(e))
        return
    except Exception as e:
        st.warning(f"Database not connected: {e}")
    
    page = sidebar_nav()
    
    if page == "Projects":
        page_projects()
    elif page == "Requirements":
        page_requirements()
    elif page == "Block Settings":
        page_block_settings()
    elif page == "Editor":
        page_editor()
    elif page == "Versions":
        page_versions()


if __name__ == "__main__":
    main()
