"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const routes = [
  { href: "/", label: "Dashboard" },
  { href: "/predict", label: "Predict" },
  { href: "/teams", label: "Teams" },
  { href: "/players", label: "Players" },
  { href: "/model", label: "Model" },
];

export function SiteNav() {
  const pathname = usePathname();

  return (
    <nav className="top-nav" aria-label="Primary">
      {routes.map((route) => {
        const isActive = pathname === route.href;
        return (
          <Link
            key={route.href}
            href={route.href}
            className={isActive ? "nav-link nav-link--active" : "nav-link"}
          >
            {route.label}
          </Link>
        );
      })}
    </nav>
  );
}
