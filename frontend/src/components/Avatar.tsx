import { avatarColor, initials } from '../lib/utils'

export default function Avatar({ name, size = 48 }: { name: string; size?: number }) {
  return (
    <div
      className="rounded-xl flex items-center justify-center font-bold text-white flex-shrink-0"
      style={{ width: size, height: size, background: avatarColor(name), fontSize: size * 0.38 }}
    >
      {initials(name)}
    </div>
  )
}
