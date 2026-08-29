import Section1 from "./section1/Section1";
import Section3 from "./section-3/Section3";
import Section2 from "./section-2/Section2";
import Section6 from "./section-6/Section6";
import Footer from "./footer/Footer";

export default function HomePage() {
  return (
    <main>
      <Section1 />
      <Section3 />
      <Section2 />
      <Section6 />
      <Footer />
    </main>
  );
}
