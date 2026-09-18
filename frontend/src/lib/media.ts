/**
 * Typed media registry — single source for all creative assets.
 * Replaces scattered "/media/..." strings; enables redesign via one file.
 */
export const F1_MEDIA = {
  videos: {
    monaco: "/media/F1_monaco.mp4",
    dusk: "/media/Formula_One_race_at_dusk_1.mp4",
  },
  hero: {
    poster: "/media/night_race.webp",
    sunset: "/media/sunset_race.webp",
    cartoon: "/media/f1_cartoon.webp",
  },
  circuits: {
    albertPark: "/media/circuit1.webp",
    monza: "/media/circuit2.webp",
  },
  podium: {
    p1: "/media/p1.webp",
    p2: "/media/p2.webp",
    p3: "/media/p3.webp",
    all: "/media/podium_all.webp",
  },
  racers: {
    r1: "/media/racer1.webp",
    r2: "/media/racer2.webp",
    r3: "/media/racer3.webp",
  },
  garage: {
    carParts: "/media/car_parts.webp",
    simulation: "/media/f1_simulation.webp",
    pitStop: "/media/pit_stop.webp",
  },
  gallery: [
    "/media/p1.webp","/media/p2.webp","/media/p3.webp","/media/podium_all.webp",
    "/media/racer1.webp","/media/racer2.webp","/media/racer3.webp","/media/circuit1.webp","/media/circuit2.webp"
  ],
} as const;
