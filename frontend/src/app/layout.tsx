import '@fontsource-variable/golos-text';
import './globals.css';
import './connected.css';
import './hr-connected.css';
import './notifications.css';
export const metadata = { title: 'Career Quest — твой путь в Halyk', description: 'Персональная карта развития сотрудника Halyk' };
export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="ru"><body>{children}</body></html>;
}
