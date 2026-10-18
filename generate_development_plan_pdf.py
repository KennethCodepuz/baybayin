from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether
)

OUT = r"C:\Users\Kenne\OneDrive\Documents\ChatGPT\Thesis-writing\output\pdf\baybayin_validator_development_plan.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=24, leading=29, alignment=TA_CENTER, textColor=colors.HexColor("#17365D"), spaceAfter=10))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontSize=12, leading=17,
    alignment=TA_CENTER, textColor=colors.HexColor("#555555")))
styles.add(ParagraphStyle(name="H1Blue", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=15, leading=19, textColor=colors.HexColor("#17365D"), spaceBefore=10, spaceAfter=7))
styles.add(ParagraphStyle(name="H2Blue", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=11.5, leading=14, textColor=colors.HexColor("#1F4E79"), spaceBefore=7, spaceAfter=4))
styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=8.8, leading=11.6,
    spaceAfter=6))
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.3, leading=10.8))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontSize=10, leading=14,
    leftIndent=9, rightIndent=9, borderColor=colors.HexColor("#9CC2E5"), borderWidth=0.8,
    borderPadding=8, backColor=colors.HexColor("#EAF3F8"), spaceBefore=6, spaceAfter=10))

def P(text, style="BodySmall"):
    return Paragraph(text, styles[style])

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#9CC2E5"))
    canvas.line(18*mm, 14*mm, 192*mm, 14*mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(18*mm, 9*mm, "Baybayin Hybrid Validator - Development Plan")
    canvas.drawRightString(192*mm, 9*mm, f"Page {doc.page}")
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
    topMargin=18*mm, bottomMargin=20*mm)
story = []
story += [Spacer(1, 35*mm), P("DEVELOPMENT PLAN", "CoverTitle"),
          P("Hybrid Baybayin Character and Stroke Validation System", "CoverSub"), Spacer(1, 8*mm),
          P("Prepared to guide Chapter 3 methodology and system implementation", "CoverSub"), Spacer(1, 22*mm),
          P("Core principle", "H2Blue"),
          P("The validator makes its decisions through defined character and stroke checks. The knowledge graph and RAG layer retrieve KWF-grounded evidence and explanations; they do not replace the measurable validation logic.", "Callout"),
          P("Research alignment", "H2Blue"),
          P("The plan directly supports the study objectives: (1) build a labeled Baybayin dataset with stroke-level information, (2) develop a stroke-based validation model, and (3) evaluate it against expert-reviewed ground truth.", "BodySmall"),
          PageBreak()]

story += [P("1. Development architecture", "H1Blue"),
          P("The system is developed in two connected versions. Version 1 establishes reliable character-form validation and the data-capture workflow. Version 2 adds the stroke-level validation required by the thesis.", "BodySmall")]

arch_data = [
    [P("Component", "Small"), P("Purpose", "Small"), P("Primary output", "Small")],
    [P("KWF reference standard", "Small"), P("Defines valid character forms, strokes, and kudlit rules.", "Small"), P("Character specification and validation rubric.", "Small")],
    [P("Knowledge graph + RAG", "Small"), P("Retrieves verified text, images, rules, and later instructional media.", "Small"), P("Evidence-based explanation.", "Small")],
    [P("Version 1: form validator", "Small"), P("Checks whether a completed drawing resembles its intended character.", "Small"), P("Form-valid/form-invalid result.", "Small")],
    [P("Version 2: stroke validator", "Small"), P("Checks count, order, direction, trajectory, and kudlit placement.", "Small"), P("Specific formation-error feedback.", "Small")],
    [P("Expert evaluation", "Small"), P("Reviews labels and validates model output against ground truth.", "Small"), P("Performance evidence for Chapter 4.", "Small")],
]
table = Table(arch_data, colWidths=[39*mm, 78*mm, 49*mm], repeatRows=1)
table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1F4E79")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#B7C9D6")),
    ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F7FAFC"), colors.white]),
    ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story += [table, Spacer(1, 8*mm), P("Implementation flow", "H2Blue"),
          P("KWF rules + reference images -> knowledge graph -> drawing canvas captures final form and online stroke data -> form and stroke checks -> RAG retrieves the relevant rule -> user receives a valid/invalid result with a specific explanation.", "Callout")]

story += [P("2. Iterative development plan", "H1Blue")]
iterations = [
    ("Iteration 1 - Requirements and standards", "Select supported characters; convert KWF material into character specifications; define valid and invalid writing; prepare an expert validation rubric.", "Approved character specification and rubric."),
    ("Iteration 2 - Knowledge base", "Create a multimodal knowledge graph with character records, reference images, writing rules, kudlit rules, common errors, and sources.", "Queryable, source-traceable knowledge base."),
    ("Iteration 3 - Version 1 form validator", "Build the drawing canvas; store the final image and raw event data; normalize the drawing; compare the final form with its reference.", "Working alphabet/form-conformance prototype."),
    ("Iteration 4 - Dataset collection and labels", "Collect correct and controlled-error samples; capture coordinates, timestamps, and pen-down/pen-up events; have an expert review labels.", "Expert-reviewed stroke-level dataset."),
    ("Iteration 5 - Version 2 stroke validator", "Segment strokes; extract features; compare order, direction, trajectories, spatial relations, and kudlit placement with the reference.", "Hybrid stroke-based validator."),
    ("Iteration 6 - Evaluation and integration", "Test on held-out participant data; calculate metrics; review errors; connect feedback to the knowledge graph and RAG layer.", "Final prototype and Chapter 4-ready results."),
]
for title, activity, output in iterations:
    story += [P(title, "H2Blue"), P(f"<b>Activities:</b> {activity}<br/><b>Output:</b> {output}", "BodySmall")]

story += [P("3. Chapter 3 methodology mapping", "H1Blue"),
          P("Chapter 3 should document the plan as a reproducible method. It must describe what will be done, the input to each stage, the activity performed, and the output produced - not the final results.", "Callout")]
mapping = [
    [P("Chapter 3 section", "Small"), P("What it documents", "Small")],
    [P("3.1 Research Design", "Small"), P("R&D design with an experimental performance-evaluation component; two connected validator versions.", "Small")],
    [P("3.2 Participants and Data Sources", "Small"), P("Volunteer writers, expert reviewer, and KWF documentary sources.", "Small")],
    [P("3.3 Research Instruments", "Small"), P("Drawing canvas, task sheet, expert checklist, knowledge graph, and evaluation tools.", "Small")],
    [P("3.4 System Development Method", "Small"), P("Agile iterations and their testable deliverables.", "Small")],
    [P("3.5 Hybrid Model Development", "Small"), P("Data acquisition, cleaning, feature extraction, model development, evaluation, and utilization.", "Small")],
    [P("3.6 Ethics and Data Management", "Small"), P("Informed consent, anonymization, restricted access, and data traceability.", "Small")],
]
table2 = Table(mapping, colWidths=[54*mm, 112*mm], repeatRows=1)
table2.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1F4E79")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#B7C9D6")), ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F7FAFC"), colors.white]),
    ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story += [table2, Spacer(1, 8*mm), P("4. Model-development stages", "H1Blue")]
stages = [
    ("Data acquisition", "Inputs: KWF reference material, participant drawings, expert rubric. Activities: build character specifications, capture final images and online trajectories, and review labels. Output: a labeled multimodal dataset."),
    ("Preprocessing", "Inputs: raw drawings and event records. Activities: remove incomplete records, normalize images and coordinates, segment strokes, preserve relative kudlit position, and resample trajectories. Output: clean and comparable samples."),
    ("Feature extraction and retrieval", "Inputs: normalized data and knowledge graph. Activities: derive form features, stroke count/order/direction/shape/spatial features, and retrieve supporting KWF references. Output: validation features plus evidence."),
    ("Modeling and evaluation", "Inputs: features, rules, reference trajectories, and labels. Activities: form comparison; rule checks; trajectory similarity; participant-level data splitting; expert-ground-truth comparison. Output: measured model performance."),
    ("Model utilization", "Inputs: a user drawing and selected target character. Activities: validate, retrieve relevant rules, and present feedback. Output: a user-facing valid/invalid result with a specific explanation."),
]
for title, detail in stages:
    story += [P(title, "H2Blue"), P(detail, "BodySmall")]

story += [P("5. Evaluation plan", "H1Blue"),
          P("Evaluate the form validator and stroke validator separately, then assess the complete hybrid system. Compare every decision with expert-reviewed ground truth. Report accuracy, precision, recall, F1-score, confusion matrices, and error-specific results for form, count, order, direction, and kudlit placement. Evaluate RAG retrieval separately for source correctness and feedback relevance. Record response time if practical feedback is a project goal.", "BodySmall"),
          P("Immediate next action", "H2Blue"),
          P("Complete Iteration 1 first: choose the initial character set and produce the character specification and expert validation rubric. These define what counts as valid before any model, knowledge graph, or dataset can be trusted.", "Callout"),
          P("Implementation decisions to confirm", "H2Blue"),
          P("1. Initial character scope: identify the exact KWF character set and whether kudlit variants are included in the first evaluation.<br/>2. Ground truth: name the qualified Baybayin expert or reviewers and agree on the labeling procedure.<br/>3. Dataset protocol: set the number of writers, repetitions per character, and controlled error categories before collection.<br/>4. Validation thresholds: establish the rule tolerances and trajectory-similarity thresholds using the validation subset, not the final test data.<br/>5. Prototype boundary: state that Version 1 establishes form conformance and Version 2 delivers the thesis stroke-validation claim.", "BodySmall")]

doc.build(story, onFirstPage=footer, onLaterPages=footer)
