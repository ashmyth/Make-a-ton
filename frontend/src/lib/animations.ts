import gsap from "gsap";

export function animatePress(element: HTMLElement | null) {
  if (!element) return;
  gsap.fromTo(
    element,
    { scale: 0.95 },
    { scale: 1, duration: 0.35, ease: "elastic.out(1, 0.4)" }
  );
}

export function animateElasticPress(element: HTMLElement | null) {
  animatePress(element);
}

export function animateHoverEnter(element: HTMLElement | null) {
  if (!element) return;
  gsap.to(element, { scale: 1.02, duration: 0.2, ease: "power1.out" });
}

export function animateHoverLeave(element: HTMLElement | null) {
  if (!element) return;
  gsap.to(element, { scale: 1, duration: 0.2, ease: "power1.out" });
}

export function animateSuccessBounce(element: HTMLElement | null) {
  if (!element) return;
  gsap.fromTo(
    element,
    { y: -6 },
    { y: 0, duration: 0.4, ease: "bounce.out" }
  );
}
