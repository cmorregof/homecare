import Image from "next/image";

/**
 * The project's cover illustration as a band on the patient's home.
 *
 * Deliberately slim (6:1 against a 4:1 source, so it crops top and bottom
 * rather than sides) and placed below the page header: this screen exists to
 * show a risk tier and a set of vitals, and a full-height hero would push both
 * under the fold. The artwork sets the tone; it does not take the page.
 *
 * No text is laid over it. The family sits across the left of the frame and
 * any readable scrim would cover exactly the gesture the picture is about.
 */
export function WelcomeBanner() {
  return (
    <div className="relative mb-5 aspect-[6/1] w-full overflow-hidden rounded-lg border border-border">
      <Image
        src="/carmen-portada.jpg"
        alt="Una familia campesina en los Andes colombianos; la abuela toma la presión arterial al abuelo en el corredor de la casa."
        fill
        sizes="(max-width: 1280px) 100vw, 1140px"
        className="object-cover object-center"
      />
    </div>
  );
}
