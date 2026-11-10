# utils/nettoyage_html.py
"""Réduit un fragment HTML à une mise en forme inoffensive.

Les notes de réunion sont affichées telles quelles dans la page du projet
(`{{ note.contenu | safe }}`). Tout contenu qui n'est pas saisi dans l'éditeur
de Loova (API, import) doit donc passer par ici : seules les balises de mise en
forme sont gardées, sans attribut (sauf le lien d'un <a>), et le contenu des
<script> et <style> est jeté.
"""
from html import escape
from html.parser import HTMLParser

BALISES_GARDEES = frozenset({
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's',
    'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'li',
    'blockquote', 'pre', 'code', 'a',
})
BALISES_SANS_FERMETURE = frozenset({'br'})
# Un paragraphe ne contient pas de bloc : l'ouverture d'un de ceux-ci le referme.
BALISES_FERMANT_LE_PARAGRAPHE = frozenset({'p', 'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'blockquote', 'pre'})
BALISES_AU_CONTENU_JETE = frozenset({'script', 'style', 'iframe', 'object', 'embed', 'template'})
DEBUTS_DE_LIEN_ADMIS = ('http://', 'https://', 'mailto:')


class _Nettoyeur(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sortie = []
        self.ouvertes = []   # balises gardées, encore ouvertes
        self.jete = 0        # profondeur dans un bloc dont le contenu est jeté

    def handle_starttag(self, tag, attrs):
        if tag in BALISES_AU_CONTENU_JETE:
            self.jete += 1
            return
        if self.jete or tag not in BALISES_GARDEES:
            return
        attributs = ''
        if tag == 'a':
            lien = (dict(attrs).get('href') or '').strip()
            if lien.lower().startswith(DEBUTS_DE_LIEN_ADMIS):
                attributs = ' href="%s" target="_blank" rel="noopener noreferrer"' % escape(lien, quote=True)
        self._fermer_ce_qui_ne_s_imbrique_pas(tag)
        self.sortie.append('<%s%s>' % (tag, attributs))
        if tag not in BALISES_SANS_FERMETURE:
            self.ouvertes.append(tag)

    def _fermer_jusqu_a(self, tag):
        while self.ouvertes:
            ouverte = self.ouvertes.pop()
            self.sortie.append('</%s>' % ouverte)
            if ouverte == tag:
                break

    def _fermer_ce_qui_ne_s_imbrique_pas(self, tag):
        """Comme un navigateur : « <li>Un<li>Deux » donne deux éléments, pas un dans l'autre."""
        if tag == 'li':
            # Un <li> resté ouvert dans la même liste (pas celui d'une liste parente).
            for ouverte in reversed(self.ouvertes):
                if ouverte in ('ul', 'ol'):
                    break
                if ouverte == 'li':
                    self._fermer_jusqu_a('li')
                    break
        elif tag in BALISES_FERMANT_LE_PARAGRAPHE and 'p' in self.ouvertes:
            self._fermer_jusqu_a('p')

    def handle_startendtag(self, tag, attrs):
        if tag in BALISES_SANS_FERMETURE:
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in BALISES_AU_CONTENU_JETE:
            self.jete = max(0, self.jete - 1)
            return
        if self.jete or tag not in self.ouvertes:
            return
        # Referme aussi ce qui a été ouvert à l'intérieur et jamais refermé.
        self._fermer_jusqu_a(tag)

    def handle_data(self, data):
        if not self.jete:
            self.sortie.append(escape(data, quote=False))

    def resultat(self):
        while self.ouvertes:
            self.sortie.append('</%s>' % self.ouvertes.pop())
        return ''.join(self.sortie).strip()


def nettoyer_html(fragment):
    """Renvoie le fragment réduit aux balises de mise en forme, toutes refermées."""
    nettoyeur = _Nettoyeur()
    nettoyeur.feed(fragment or '')
    nettoyeur.close()
    return nettoyeur.resultat()


def texte_seul(fragment):
    """Texte du fragment, sans aucune balise (pour savoir s'il est vide)."""
    class _Texte(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.morceaux = []

        def handle_data(self, data):
            self.morceaux.append(data)

    lecteur = _Texte()
    lecteur.feed(fragment or '')
    lecteur.close()
    return ''.join(lecteur.morceaux).strip()
