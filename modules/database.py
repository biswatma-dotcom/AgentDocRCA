import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from modules.models import Base, Project, RequirementSet, DocBlockTemplate, DocVersion, DocChangeLog
from contextlib import contextmanager


def get_database_url():
    return os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/agentdocrca')


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    return SessionLocal()


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_project(db: Session, name: str, client_name: str = None) -> Project:
    project = Project(name=name, client_name=client_name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_projects(db: Session):
    return db.query(Project).order_by(Project.created_at.desc()).all()


def get_project(db: Session, project_id: str):
    return db.query(Project).filter(Project.id == project_id).first()


def create_requirement_set(db: Session, project_id: str, title: str, raw_text: str = None, created_by: str = None) -> RequirementSet:
    req_set = RequirementSet(
        project_id=project_id,
        title=title,
        raw_text=raw_text,
        created_by=created_by
    )
    db.add(req_set)
    db.commit()
    db.refresh(req_set)
    return req_set


def get_requirement_sets(db: Session, project_id: str):
    return db.query(RequirementSet).filter(RequirementSet.project_id == project_id).order_by(RequirementSet.created_at.desc()).all()


def get_requirement_set(db: Session, req_set_id: str):
    return db.query(RequirementSet).filter(RequirementSet.id == req_set_id).first()


def update_requirement_set_bullets(db: Session, req_set_id: str, bullets: list):
    req_set = db.query(RequirementSet).filter(RequirementSet.id == req_set_id).first()
    req_set.normalized_bullets = bullets
    db.commit()
    db.refresh(req_set)
    return req_set


def create_block_template(db: Session, project_id: str, name: str, order_index: int, placeholder: str = None, block_type: str = 'text') -> DocBlockTemplate:
    block = DocBlockTemplate(
        project_id=project_id,
        name=name,
        order_index=order_index,
        placeholder=placeholder,
        block_type=block_type
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


def get_block_templates(db: Session, project_id: str):
    return db.query(DocBlockTemplate).filter(DocBlockTemplate.project_id == project_id).order_by(DocBlockTemplate.order_index).all()


def update_block_template(db: Session, block_id: str, **kwargs):
    block = db.query(DocBlockTemplate).filter(DocBlockTemplate.id == block_id).first()
    for key, value in kwargs.items():
        setattr(block, key, value)
    db.commit()
    db.refresh(block)
    return block


def delete_block_template(db: Session, block_id: str):
    block = db.query(DocBlockTemplate).filter(DocBlockTemplate.id == block_id).first()
    db.delete(block)
    db.commit()


def get_latest_version(db: Session, project_id: str):
    return db.query(DocVersion).filter(
        DocVersion.project_id == project_id
    ).order_by(DocVersion.version_number.desc()).first()


def get_version(db: Session, version_id: str):
    return db.query(DocVersion).filter(DocVersion.id == version_id).first()


def get_all_versions(db: Session, project_id: str):
    return db.query(DocVersion).filter(
        DocVersion.project_id == project_id
    ).order_by(DocVersion.version_number.desc()).all()


def create_new_version(db: Session, project_id: str, blocks_content: dict, created_by: str = None, change_summary: str = None) -> DocVersion:
    latest = get_latest_version(db, project_id)
    version_number = (latest.version_number + 1) if latest else 1
    
    version = DocVersion(
        project_id=project_id,
        version_number=version_number,
        blocks_content=blocks_content,
        created_by=created_by,
        change_summary=change_summary
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def create_change_log(db: Session, doc_version_id: str, template_block_id: str, before_text: str, after_text: str,
                      requirement_set_id: str, requirement_bullet_indexes: list, reason_why: str, impact: str) -> DocChangeLog:
    change_log = DocChangeLog(
        doc_version_id=doc_version_id,
        template_block_id=template_block_id,
        before_text=before_text,
        after_text=after_text,
        requirement_set_id=requirement_set_id,
        requirement_bullet_indexes=requirement_bullet_indexes,
        reason_why=reason_why,
        impact=impact
    )
    db.add(change_log)
    db.commit()
    db.refresh(change_log)
    return change_log


def get_change_logs_for_version(db: Session, version_id: str):
    return db.query(DocChangeLog).filter(DocChangeLog.doc_version_id == version_id).all()
