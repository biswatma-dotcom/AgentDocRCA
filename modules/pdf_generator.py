import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle


def generate_pdf(project, version, blocks, change_logs, requirement_sets, block_templates):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,
        spaceAfter=12
    )
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=6,
        spaceBefore=12
    )
    
    story = []
    
    story.append(Paragraph("Agent Documentation", title_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"<b>Project:</b> {project.name}"))
    story.append(Paragraph(f"<b>Client:</b> {project.client_name or 'N/A'}"))
    story.append(Paragraph(f"<b>Version:</b> {version.version_number}"))
    story.append(Paragraph(f"<b>Date:</b> {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}"))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Document Content", styles['Heading1']))
    
    blocks_dict = version.blocks_content if version.blocks_content else {}
    template_dict = {str(bt.id): bt for bt in block_templates}
    
    for block in blocks:
        block_id = str(block.id)
        content = blocks_dict.get(block_id, '')
        
        story.append(Paragraph(block.name, heading2_style))
        
        if content:
            story.append(Paragraph(content.replace('\n', '<br/>')))
        else:
            story.append(Paragraph("[No content]"))
        story.append(Spacer(1, 12))
    
    if change_logs:
        story.append(PageBreak())
        story.append(Paragraph("Change Log for this Version", styles['Heading1']))
        
        for log in change_logs:
            req_set = next((rs for rs in requirement_sets if str(rs.id) == str(log.requirement_set_id)), None)
            block = template_dict.get(str(log.template_block_id), None)
            
            story.append(Paragraph(f"Block: {block.name if block else 'Unknown'}", heading2_style))
            
            story.append(Paragraph(f"<b>Requirement Set:</b> {req_set.title if req_set else 'Unknown'}"))
            
            if log.requirement_bullet_indexes and req_set and req_set.normalized_bullets:
                bullets = []
                for idx in log.requirement_bullet_indexes:
                    if idx < len(req_set.normalized_bullets):
                        bullets.append(req_set.normalized_bullets[idx])
                story.append(Paragraph(f"<b>Bullet(s):</b> {'; '.join(bullets)}"))
            
            story.append(Paragraph(f"<b>Reason:</b> {log.reason_why or 'N/A'}"))
            story.append(Paragraph(f"<b>Impact:</b> {log.impact or 'N/A'}"))
            story.append(Spacer(1, 12))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_pdf_bytes(project, version, blocks, change_logs, requirement_sets, block_templates):
    buffer = generate_pdf(project, version, blocks, change_logs, requirement_sets, block_templates)
    return buffer.getvalue()
