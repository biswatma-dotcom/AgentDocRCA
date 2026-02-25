import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Project(Base):
    __tablename__ = 'projects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    client_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    requirement_sets = relationship('RequirementSet', back_populates='project', cascade='all, delete-orphan')
    doc_block_templates = relationship('DocBlockTemplate', back_populates='project', cascade='all, delete-orphan')
    doc_versions = relationship('DocVersion', back_populates='project', cascade='all, delete-orphan')


class RequirementSet(Base):
    __tablename__ = 'requirement_sets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    raw_text = Column(Text)
    normalized_bullets = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255))

    project = relationship('Project', back_populates='requirement_sets')


class DocBlockTemplate(Base):
    __tablename__ = 'doc_block_templates'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=False)
    block_type = Column(String(50), default='text')
    placeholder = Column(Text)

    project = relationship('Project', back_populates='doc_block_templates')


class DocVersion(Base):
    __tablename__ = 'doc_versions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    version_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255))
    blocks_content = Column(JSONB, default=dict)
    change_summary = Column(Text)

    project = relationship('Project', back_populates='doc_versions')
    change_logs = relationship('DocChangeLog', back_populates='doc_version', cascade='all, delete-orphan')


class DocChangeLog(Base):
    __tablename__ = 'doc_change_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_version_id = Column(UUID(as_uuid=True), ForeignKey('doc_versions.id', ondelete='CASCADE'), nullable=False)
    template_block_id = Column(UUID(as_uuid=True), ForeignKey('doc_block_templates.id', ondelete='CASCADE'), nullable=False)
    before_text = Column(Text)
    after_text = Column(Text)
    requirement_set_id = Column(UUID(as_uuid=True), ForeignKey('requirement_sets.id', ondelete='CASCADE'), nullable=False)
    requirement_bullet_indexes = Column(JSONB, default=list)
    reason_why = Column(Text, nullable=False)
    impact = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    doc_version = relationship('DocVersion', back_populates='change_logs')
    requirement_set = relationship('RequirementSet')
    template_block = relationship('DocBlockTemplate')
