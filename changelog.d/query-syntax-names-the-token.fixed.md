- **A `QUERY_SYNTAX` error names the token the caller wrote instead of leading
  with SQLite's fragment (#67).** `detention AND third-party-doctrine` reaches
  MATCH unquoted because the query carries an operator, and SQLite answers
  `no such column: party` (a piece of a token nobody typed), which sent readers
  looking for a schema problem. The message now says the token was read as a
  column reference and shows the quoted form. When the error names a fragment no
  token of the query contains, the previous text is kept unchanged.
