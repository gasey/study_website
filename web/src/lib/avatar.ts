import { reviewRequest } from "./review";
export interface AvatarLook {
  skin: string;
  hair: string;
  hairC: string;
  top: string;
  acc: string;
  bg: string;
  frame: string;
}
export interface AvatarItem {
  id: string;
  category: keyof AvatarLook;
  label: string;
  value: string;
  level: number;
  available: boolean;
  claimed: boolean;
}
export interface AvatarAccount {
  user_id: string;
  name: string | null;
  handle: string;
  registered: boolean;
  level: number;
  avatar: AvatarLook | null;
  avatar_version: number;
  default: AvatarLook;
  catalog: AvatarItem[];
}
export const AVATAR_COLORS: Record<string, string> = {
  Vermilion: "#C0462C",
  Teal: "#1F7F86",
  Blue: "#33609E",
  Saffron: "#D8A33A",
  Committed: "#1F7F86",
  Gold: "#D8A33A",
};
export const loadAvatar = () => reviewRequest<AvatarAccount>("/me/avatar");
export const saveAvatar = (
  user_id: string,
  expected_version: number,
  look: AvatarLook | null,
) =>
  reviewRequest<{ avatar: AvatarLook | null; avatar_version: number }>(
    "/me/avatar",
    { user_id, expected_version, look },
  );
