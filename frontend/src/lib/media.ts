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
    poster: "/media/night_race.png",
    sunset: "/media/sunset_race.png",
    cartoon: "/media/f1_cartoon.png",
  },
  circuits: {
    albertPark: "/media/circuit1.png",
    monza: "/media/circuit2.png",
  },
  podium: {
    p1: "/media/p1.png",
    p2: "/media/p2.png",
    p3: "/media/p3.png",
    all: "/media/podium_all.png",
  },
  racers: {
    r1: "/media/racer1.png",
    r2: "/media/racer2.png",
    r3: "/media/racer3.png",
  },
  garage: {
    carParts: "/media/car_parts.png",
    simulation: "/media/f1_simulation.png",
    pitStop: "/media/pit_stop.jpg",
  },
  gallery: [
    "/media/p1.png","/media/p2.png","/media/p3.png","/media/podium_all.png",
    "/media/racer1.png","/media/racer2.png","/media/racer3.png","/media/circuit1.png","/media/circuit2.png"
  ],
} as const;
