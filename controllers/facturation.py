from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from decimal import Decimal

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
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from io import BytesIO
from decimal import Decimal

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

    current_y_emitter = height - 165 # Position Y de départ pour les coordonnées de contact

    p.setFont("Helvetica", 9)
    # Affichage du téléphone
    phone_text = organisation.telephone or ""
    p.drawString(
        50,
        current_y_emitter,
        f"Tel : {phone_text}"
    )
    current_y_emitter -= 15 # Décalage vers le bas pour la ligne suivante

    # Affichage de l'e-mail
    email_text = organisation.mail_contact or ""
    p.drawString(
        50,
        current_y_emitter,
        f"Mail : {email_text}"
    )
    current_y_emitter -= 15 # Décalage vers le bas pour la ligne suivante

    # Affichage de l'adresse
    p.drawString(
        50,
        current_y_emitter, # Anciennement height - 180
        f"{organisation.adresse}, {organisation.code_postal} {organisation.ville}"
    )
    current_y_emitter -= 15 # Décalage vers le bas pour la ligne suivante

    # Ajout du numéro SIRET de l'organisation s'il existe
    if hasattr(organisation, 'siret') and organisation.siret:
        p.drawString(
            50,
            current_y_emitter,  # Anciennement height - 195
            f"SIRET : {organisation.siret}"
        )
        current_y_emitter -= 15

    # ======================
    # COORDONNÉES CLIENT
    # ======================
    # (à droite, sous le bloc "Facture n°")
    p.setFont("Helvetica-Bold", 9)
    p.drawRightString(width - 50, height - 150, "À L'ATTENTION DE")
    p.setFont("Helvetica", 9)

    # Utilisation des informations du client
    client_nom = client.nom if client and client.nom else "Client inconnu"
    client_adresse = client.adresse if client and client.adresse else "Adresse inconnue"
    # Ensure client_tel is a string, even if None or client is None
    client_tel = client.telephone if client and client.telephone else ""

    p.drawRightString(width - 50, height - 165, client_nom)
    p.drawRightString(width - 50, height - 180, client_tel)
    p.drawRightString(width - 50, height - 195, client_adresse)

    # ======================
    #   TABLEAU D'ARTICLES
    # ======================
    # Position de départ du tableau
    header_baseline_y = height - 230
    left_margin = 50
    right_margin = width - 50
    col_widths = [(right_margin - left_margin) * 0.45,  # DESCRIPTION
                  (right_margin - left_margin) * 0.15,  # PRIX
                  (right_margin - left_margin) * 0.15,  # QTE
                  (right_margin - left_margin) * 0.25]  # TOTAL
    
    # Calcul des positions X pour les colonnes (début de chaque colonne)
    x_positions = [left_margin]
    temp_x = left_margin
    for width_col in col_widths:
        temp_x += width_col
        x_positions.append(temp_x)
    # x_positions sera [left_margin, left_margin + w0, left_margin + w0 + w1, ...]
    # x_positions[0] = début col DESCRIPTION
    # x_positions[1] = début col PRIX (et fin col DESCRIPTION)
    # x_positions[2] = début col QUANTITÉ (et fin col PRIX)
    # x_positions[3] = début col TOTAL (et fin col QUANTITÉ)
    # x_positions[4] = fin col TOTAL (équivalent à right_margin)

    # --- En-têtes du tableau ---
    p.setFont("Helvetica-Bold", 10)
    headers = ["DESCRIPTION", "PRIX", "QUANTITÉ", "TOTAL"]

    p.drawString(x_positions[0] + 2, header_baseline_y, headers[0]) # DESCRIPTION (left-aligned)
    p.drawRightString(x_positions[2] - 5, header_baseline_y, headers[1]) # PRIX (right-aligned)
    p.drawRightString(x_positions[3] - 5, header_baseline_y, headers[2]) # QUANTITÉ (right-aligned)
    p.drawRightString(x_positions[4] - 5, header_baseline_y, headers[3]) # TOTAL (right-aligned)


    # Ligne sous l'en-tête
    p.setLineWidth(1)
    line_y_after_headers = header_baseline_y - 5
    p.line(left_margin, line_y_after_headers, right_margin, line_y_after_headers)
    
    current_row_top_y = line_y_after_headers - 5 # Top of the first item row area, with 5pt padding


    # Utilisation des informations de la transaction pour les articles
    items = [
        {
            "description": transaction.description,
            "prix": transaction.montant,
            "quantite": 1,  # Par défaut, on considère une quantité de 1 pour une transaction
        }
    ]

    # Style pour la description des articles (pour le wrapping)
    styles = getSampleStyleSheet()
    item_font_size = 10
    item_leading = 12 # Espace entre les lignes de base pour la police de taille 10
    item_desc_style = ParagraphStyle(
        'item_desc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=item_font_size,
        leading=item_leading
    )
    row_padding_below_content = 3 # Espace vertical entre les articles


    p.setFont("Helvetica", 10)
    sous_total = 0

    for item in items:
        desc = item["description"]
        prix = item["prix"]
        qte = item["quantite"]
        total_ligne = Decimal(prix) * Decimal(qte) # Assurer calcul Decimal
        sous_total += total_ligne

        # DESCRIPTION (avec Paragraph pour le retour à la ligne)
        desc_paragraph = Paragraph(desc, item_desc_style)
        desc_w, desc_h = desc_paragraph.wrapOn(p, col_widths[0] - 4, 0) # -4 pour petite marge interne
        desc_paragraph.drawOn(p, x_positions[0] + 2, current_row_top_y - desc_h)

        # PRIX, QUANTITÉ, TOTAL (alignés avec la première ligne de la description)
        other_cells_baseline_y = current_row_top_y - item_font_size
        p.drawRightString(x_positions[2] - 5, other_cells_baseline_y, f"{prix} €")
        p.drawRightString(x_positions[3] - 5, other_cells_baseline_y, str(qte))
        p.drawRightString(x_positions[4] - 5, other_cells_baseline_y, f"{total_ligne} €")

        current_row_top_y -= (desc_h + row_padding_below_content)


    # Ligne horizontale après les articles
    line_y_after_items = current_row_top_y + row_padding_below_content - 2 # Placer la ligne juste au-dessus du prochain espace
    p.line(left_margin, line_y_after_items, right_margin, line_y_after_items)
    
    summary_baseline_y = line_y_after_items - 20 # Espace avant le bloc de résumé


    # ======================
    #   RÉCAPITULATIF
    # ======================
    # Exemples de calcul
    tva_rate = Decimal('0.20')  # TODO : Solution pour adapter la TVA
    if organisation.exonere_tva:
        tva_amount = 0
        total_ttc = sous_total
    else:
        tva_amount = sous_total * tva_rate
        total_ttc = sous_total + tva_amount

    p.setFont("Helvetica-Bold", 10)
    p.drawRightString(x_positions[2], summary_baseline_y, "SOUS-TOTAL :") # x_positions[2] est la fin de la col PRIX
    p.drawRightString(x_positions[4] - 5, summary_baseline_y, f"{sous_total} €")
    summary_baseline_y -= 15

    if not organisation.exonere_tva:
        p.drawRightString(x_positions[2], summary_baseline_y, "TVA (20%) :")
        p.drawRightString(x_positions[4] - 5, summary_baseline_y, f"{tva_amount:.2f} €")
        summary_baseline_y -= 15

    p.drawRightString(x_positions[2], summary_baseline_y, "TOTAL TTC :")
    p.drawRightString(x_positions[4] - 5, summary_baseline_y, f"{total_ttc:.2f} €")
    summary_baseline_y -= 15

    # Mention légale si TVA non applicable
    if organisation.exonere_tva:
        p.setFont("Helvetica", 8)
        p.drawRightString(x_positions[4] - 5, summary_baseline_y, "TVA non applicable, article 293 B du Code général des impôts (CGI)")
        summary_baseline_y -=15

    # ======================
    #   PAIEMENT / FOOTER
    # ======================
    current_y = summary_baseline_y - 25
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


    # ======================
    # COORDONNÉES CLIENT
    # ======================
    # (à droite, sous le bloc "Facture n°")
    p.setFont("Helvetica-Bold", 9)
    p.drawRightString(width - 50, height - 150, "À L'ATTENTION DE")
    p.setFont("Helvetica", 9)

    # Utilisation des informations du client
    client_nom = client.nom if client and client.nom else "Client inconnu"
    client_adresse = client.adresse if client and client.adresse else "Adresse inconnue"
    # Ensure client_tel is a string, even if None or client is None
    client_tel = client.telephone if client and client.telephone else ""

    p.drawRightString(width - 50, height - 165, client_nom)
    p.drawRightString(width - 50, height - 180, client_tel)
    p.drawRightString(width - 50, height - 195, client_adresse)

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
    tva_rate = Decimal('0.20')  # TODO : Solution pour adapter la TVA
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
