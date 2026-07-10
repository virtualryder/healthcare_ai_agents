# Leave-behinds — one-page PDFs

Print-ready, one-page summaries for each agent: the issue, three cost stats, the governed pipeline,
the outcomes, and the bright line — with an optional logo slot (internal-track only). Hand one to a stakeholder after the
meeting. Regenerate: `NODE_PATH=<...>/node_modules node ../build-leave-behinds.js && soffice --headless --convert-to pdf *.pptx`.
