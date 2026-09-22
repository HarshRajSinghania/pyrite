- **The single-KB investigation tools serve nothing when the caller may not
  read the KB they resolve to (#223).** Twelve read tools -- `investigation_timeline`,
  `investigation_entities`, `investigation_network`, `investigation_sources`,
  `investigation_claims`, `investigation_evidence_chain`,
  `investigation_export_pack`, `investigation_money_flow`,
  `investigation_qa_report`, `investigation_ownership_chain`,
  `investigation_ftm_export`, `investigation_status` -- settle on one KB when
  none is named: the caller's, or the plugin's own default. A scoped caller was
  refused those calls rather than served a KB they may not read. Each resolves
  through a guard now, which answers with a KB name that matches no entry when
  the resolved KB is not readable, so the tool keeps its normal shape with
  nothing in it. The write-path tools in the same extension keep the
  fail-closed listing, because a caller who may write a KB can read it.
