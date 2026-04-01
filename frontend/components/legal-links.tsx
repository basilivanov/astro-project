import Link from "next/link";

type LegalLinksProps = {
  className?: string;
  linkClassName?: string;
};

export const LEGAL_PUBLIC_DOMAIN = "app.astrograce.ru";
export const LEGAL_IDENTITY = {
  owner: "ИП Иванов Василий Александрович",
  inn: "774300091472",
  ogrnip: "313574924700061",
  domain: LEGAL_PUBLIC_DOMAIN,
} as const;

export function LegalIdentityBlock({ className = "" }: { className?: string }) {
  return (
    <div className={className}>
      <p className="font-semibold text-slate-700">{LEGAL_IDENTITY.owner}</p>
      <p>ИНН {LEGAL_IDENTITY.inn} · ОГРНИП {LEGAL_IDENTITY.ogrnip}</p>
      <p>Домен сервиса: {LEGAL_IDENTITY.domain}</p>
    </div>
  );
}

export function LegalFooterBlock({ className = "", compact = false }: { className?: string; compact?: boolean }) {
  return (
    <div className={className}>
      <LegalIdentityBlock className={compact ? "space-y-1" : "space-y-1.5"} />
      <LegalLinks
        className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2"
        linkClassName="font-medium text-purple-700 transition-colors hover:text-purple-800"
      />
    </div>
  );
}

export default function LegalLinks({ className = "", linkClassName = "" }: LegalLinksProps) {
  return (
    <div className={className}>
      <Link href="/legal/terms" className={linkClassName}>Оферта</Link>
      <Link href="/legal/privacy" className={linkClassName}>Privacy / ПДн</Link>
      <Link href="/legal/consent" className={linkClassName}>Consent</Link>
      <Link href="/legal/payments" className={linkClassName}>Оплата и возвраты</Link>
    </div>
  );
}
