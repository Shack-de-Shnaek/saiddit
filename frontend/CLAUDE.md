# Frontend conventions

- **shadcn-vue is installed. Always prefer shadcn components/elements/styling** over hand-rolled
  markup. Before writing a button, input, card, dialog, form, etc., use the shadcn component
  (`@/components/ui/...`); add missing ones with `npx shadcn-vue@latest add <component>`.
  Only hand-roll when shadcn has no equivalent.
- Plain JavaScript only — no TypeScript, no JSDoc typedefs.
- Use the `@/` alias for imports and the `cn()` helper from `@/lib/utils` for class merging.
- Stick to the theme tokens (`bg-background`, `text-muted-foreground`, ...) from `src/style.css`.
