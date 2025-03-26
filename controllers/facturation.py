from fpdf import FPDF

def generer_facture(projet_nom, transactions):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Facture pour le projet : {projet_nom}", ln=1, align="C")

    for transaction in transactions:
        pdf.cell(200, 10, txt=f"{transaction.description} : {transaction.montant} ({transaction.type})", ln=1)

    pdf.output("facture.pdf")
    return "facture.pdf"
