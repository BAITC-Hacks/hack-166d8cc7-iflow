import Link from "next/link";
import "./globals.css";
import {SessionProvider} from "@/components/session-provider";
export const metadata={title:"Career Quest",description:"Employee development navigator"};
export default function Layout({children}:{children:React.ReactNode}) {
 return <html lang="en"><body><main><header><h1>Career Quest</h1><nav><Link href="/">Employees</Link><Link href="/hr">HR view</Link></nav></header><SessionProvider>{children}</SessionProvider></main></body></html>;
}
