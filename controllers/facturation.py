from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from io import BytesIO

from controllers.db_manager import db


def generate_facturation_pdf(transaction):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Récupérer les informations de l'organisation
    organisation = transaction.user.organisation
    projet = transaction.projet
    client = projet.client

    # ======================
    #        EN-TÊTE
    # ======================
    # Logo (si présent)
    if organisation.logo:
        try:
            logo_image = ImageReader(BytesIO(organisation.logo))
            # Ajuste la position/ taille selon tes préférences
            p.drawImage(
                logo_image,
                x=50,
                y=height - 120,
                width=70,
                height=70,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception as e:
            print(f"Error loading logo: {e}")
            # Gérer l'erreur ou insérer un logo par défaut si besoin

    # Numéro de facture + date (en haut à droite)
    p.setFont("Helvetica-Bold", 12)
    facture_num = f"Facture n° {transaction.id}"  # Utilisation de l'ID de la transaction comme numéro de facture
    p.drawRightString(width - 50, height - 50, facture_num)

    facture_date = transaction.date.strftime('%d/%m/%Y')
    p.setFont("Helvetica", 10)
    p.drawRightString(width - 50, height - 65, facture_date)

    # ======================
    # COORDONNÉES ÉMETTEUR
    # ======================
    # (à gauche, sous le logo)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, height - 150, organisation.designation)

    p.setFont("Helvetica", 9)
    p.drawString(
        50,
        height - 165,
        f"{organisation.telephone} | {organisation.mail_contact}"
    )
    p.drawString(
        50,
        height - 180,
        f"{organisation.adresse}, {organisation.code_postal} {organisation.ville}"
    )

    # ======================
    # COORDONNÉES CLIENT
    # ======================
    # (à droite, sous le bloc "Facture n°")
    p.setFont("Helvetica-Bold", 9)
    p.drawRightString(width - 50, height - 150, "À L'ATTENTION DE")
    p.setFont("Helvetica", 9)

    # Utilisation des informations du client
    client_name = client.nom
    client_tel = client.telephone
    client_address = f"{client.adresse}, {client.code_postal} {client.ville}"

    p.drawRightString(width - 50, height - 165, client_name)
    p.drawRightString(width - 50, height - 180, client_tel)
    p.drawRightString(width - 50, height - 195, client_address)

    # ======================
    #   TABLEAU D'ARTICLES
    # ======================
    # Position de départ du tableau
    table_top = height - 230
    left_margin = 50
    right_margin = width - 50
    col_widths = [(right_margin - left_margin) * 0.45,  # DESCRIPTION
                  (right_margin - left_margin) * 0.15,  # PRIX
                  (right_margin - left_margin) * 0.15,  # QTE
                  (right_margin - left_margin) * 0.25]  # TOTAL

    # En-têtes du tableau
    p.setFont("Helvetica-Bold", 10)
    headers = ["DESCRIPTION", "PRIX", "QUANTITÉ", "TOTAL"]

    # Dessin de l'en-tête
    current_y = table_top
    x_positions = [left_margin]
    for i, width_col in enumerate(col_widths):
        x_positions.append(x_positions[-1] + width_col)
        p.drawString(x_positions[-2] + 2, current_y, headers[i])

    # Ligne sous l'en-tête
    p.setLineWidth(1)
    p.line(left_margin, current_y - 5, right_margin, current_y - 5)
    current_y -= 20

    # Utilisation des informations de la transaction pour les articles
    items = [
        {
            "description": transaction.description,
            "prix": transaction.montant,
            "quantite": 1,  # Par défaut, on considère une quantité de 1 pour une transaction
        }
    ]

    p.setFont("Helvetica", 10)
    sous_total = 0

    for item in items:
        desc = item["description"]
        prix = item["prix"]
        qte = item["quantite"]
        total_ligne = prix * qte
        sous_total += total_ligne

        # DESCRIPTION
        p.drawString(x_positions[0] + 2, current_y, desc)
        # PRIX (aligné à droite)
        p.drawRightString(x_positions[2] - 5, current_y, f"{prix} €")
        # QUANTITÉ (aligné à droite)
        p.drawRightString(x_positions[3] - 5, current_y, str(qte))
        # TOTAL (aligné à droite)
        p.drawRightString(x_positions[4] - 5, current_y, f"{total_ligne} €")

        current_y -= 15

    # Ligne horizontale après les articles
    p.line(left_margin, current_y - 5, right_margin, current_y - 5)
    current_y -= 25

    # ======================
    #   RÉCAPITULATIF
    # ======================
    # Exemples de calcul
    tva_rate = 0.20  # 20% de TVA, par exemple
    if organisation.exonere_tva:
        tva_amount = 0
        total_ttc = sous_total
    else:
        tva_amount = sous_total * tva_rate
        total_ttc = sous_total + tva_amount

    p.setFont("Helvetica-Bold", 10)
    p.drawRightString(x_positions[2], current_y, "SOUS-TOTAL :")
    p.drawRightString(x_positions[4] - 5, current_y, f"{sous_total} €")
    current_y -= 15

    if not organisation.exonere_tva:
        p.drawRightString(x_positions[2], current_y, "TVA (20%) :")
        p.drawRightString(x_positions[4] - 5, current_y, f"{tva_amount:.2f} €")
        current_y -= 15

    p.drawRightString(x_positions[2], current_y, "TOTAL TTC :")
    p.drawRightString(x_positions[4] - 5, current_y, f"{total_ttc:.2f} €")
    current_y -= 15

    # Mention légale si TVA non applicable
    if organisation.exonere_tva:
        p.setFont("Helvetica", 8)
        p.drawRightString(x_positions[4] - 5, current_y, "TVA non applicable, article 293 B du Code général des impôts (CGI)")
        current_y -=15

    # ======================
    #   PAIEMENT / FOOTER
    # ======================
    current_y -= 25
    p.setFont("Helvetica", 9)
    p.drawString(left_margin, current_y, f"Paiement à l'ordre de {organisation.designation}")
    current_y -= 15
    p.drawString(left_margin, current_y, f"IBAN : {organisation.iban} | BIC : {organisation.bic}")
    current_y -= 15
    p.drawString(left_margin, current_y, "Paiement sous 30 jours. Des pénalités peuvent s'appliquer en cas de retard.")

    # Message de remerciement en bas de page
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width / 2, 50, "Merci pour votre confiance et à bientôt !")

    # Finaliser la page et sauvegarder
    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()
