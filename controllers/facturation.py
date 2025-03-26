from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib.utils import ImageReader
from flask import url_for

def generate_facturation_pdf(transaction):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Retrieve organization information from the transaction's user
    organisation = transaction.user.organisation

    # --- Logo ---
    if organisation.logo:
        try:
            # Use ImageReader to handle binary data
            logo_image = ImageReader(BytesIO(organisation.logo))
            # Draw the image on the canvas (adjust position and size as needed)
            p.drawImage(logo_image, 50, height - 150, width=100, height=100, preserveAspectRatio=True)
        except Exception as e:
            print(f"Error loading logo: {e}")
            # Handle the error, e.g., log it or use a default image
    # --- End Logo ---

    # En-tête : Nom de l'entreprise et coordonnées
    p.setFont("Helvetica-Bold", 16)
    p.drawString(170, height - 50, organisation.designation)  # Use organization's designation
    p.setFont("Helvetica", 10)
    p.drawString(170, height - 70, f"{organisation.adresse}, {organisation.code_postal} {organisation.ville}, {organisation.telephone}, {organisation.mail_contact}") # Use organization's details

    # Titre de la facture
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2, height - 100, "FACTURE")

    # Ligne horizontale pour séparer l'en-tête du contenu
    p.setLineWidth(1)
    p.line(50, height - 110, width - 50, height - 110)

    # Section Détails de la transaction
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 140, "Détails de la transaction:")
    
    p.setFont("Helvetica", 10)
    y = height - 160  # Position initiale pour les détails
    line_height = 15

    p.drawString(60, y, f"ID de la transaction : {transaction.id}")
    y -= line_height
    p.drawString(60, y, f"Date : {transaction.date.strftime('%d/%m/%Y')}")
    y -= line_height
    p.drawString(60, y, f"Type : {transaction.type}")
    y -= line_height
    p.drawString(60, y, f"Montant : {transaction.montant} €")
    y -= line_height
    p.drawString(60, y, f"Description : {transaction.description}")
    y -= line_height
    p.drawString(60, y, f"Mode de paiement : {transaction.mode_paiement}")

    # Ajout d'une section optionnelle pour plus d'informations (ex : conditions de paiement)
    y -= (line_height * 2)
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(50, y, "Conditions de paiement : Paiement à 30 jours. Merci de votre confiance.")

    # Pied de page : Message de remerciement
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width/2, 50, "Merci pour votre confiance et à bientôt !")

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()
