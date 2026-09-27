import { SITE_COPYRIGHT, SITE_FOOTER_NOTE } from "@/constants/content";

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-border pt-8 pb-6 text-center">
      <p className="text-sm text-muted">{SITE_COPYRIGHT}</p>
      <p className="mx-auto mt-2 max-w-xl text-xs leading-relaxed text-muted/80">
        {SITE_FOOTER_NOTE}
      </p>
    </footer>
  );
}
