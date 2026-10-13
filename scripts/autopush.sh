#!/usr/bin/env bash
# Auto-commit + push. Lo ejecuta el hook "Stop" de Claude Code cuando Claude termina de responder.
# Nunca falla el hook (siempre sale con código 0).
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
[ -z "$(git status --porcelain)" ] && exit 0                     # nada que subir

git add -A
files=$(git diff --cached --name-only | head -6 | paste -sd, - | sed 's/,/, /g')
total=$(git diff --cached --name-only | wc -l | tr -d ' ')
git commit -q -m "Actualización $(date '+%Y-%m-%d %H:%M')" -m "Archivos ($total): $files" \
  || { echo "[autopush] no se pudo crear el commit" >&2; exit 0; }
echo "[autopush] commit creado ($total archivo/s)" >&2

if git remote | grep -qx origin; then
  if git push -q 2>/dev/null || git push -q -u origin HEAD 2>/dev/null; then
    echo "[autopush] subido a GitHub" >&2
  else
    echo "[autopush] el push falló (¿sin internet o sin permisos?); el commit quedó local" >&2
  fi
else
  echo "[autopush] sin remoto 'origin': solo commit local" >&2
fi
exit 0
