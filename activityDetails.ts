interface Image {
  url: string;
  description: string | null;
  alt: string | null;
  width: number;
  height: number;
}

interface Price {
  marketPrice: string;
  sellingPrice: string;
  currency: string;
}

interface Location {
  address: string;
  coordinates: string;
  imageUrl: string;
}

interface Review {
  count: number;
  score: number;
  description: string;
}

interface BreadCrumb {
  name: string;
  url: string;
}

interface ActivityDetails {
  id: number;
  title: string;
  url: string;
  description: string;
  summary: string;
  highlights: string[];
  price: Price;
  location: Location;
  review: Review;
  noPastParticipants: string;
  images: Image[];
  breadcrumbs: BreadCrumb[];
}