# Status prac

## Zrobione

- Przygotowano lokalny branch `design/milan-dark-gold` z ciemną paletą i
  typografią; układ strony pozostał bez zmian.
- Herb `static/club/images/milan.svg` pozostaje nienaruszony.
- Na stronie Historii dodano responsywną oś czasu z 14 wydarzeniami klubu,
  złotym postępem linii, podświetlaniem odwiedzonych punktów i autorską piłką
  SVG `static/club/images/milan-timeline-ball.svg`.
- Pełny opis historii z CMS jest dostępny pod osią w rozwijanej sekcji.
- Dodano test obecności i dostępności osi czasu.
- Weryfikacja: `manage.py check` bez problemów, 7 testów zaliczonych,
  `git diff --check` bez błędów.
- Lokalny serwer Django na `127.0.0.1:8000` został zatrzymany.

## Do zrobienia

- Przejrzeć zmiany na branchu `design/milan-dark-gold` i zdecydować o commicie
  oraz dalszym połączeniu z gałęzią główną.
