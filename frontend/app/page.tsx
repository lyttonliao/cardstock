import { redirect } from "next/navigation";
import Image from "next/image";

export default function HomePage() {
  return (
    <div className="w-screen relative left-1/2 -translate-x-1/2 animate-pulse [animation-duration:4s] -mt-8">
      <Image src="/Pulse.png" alt="banner" width={1920} height={450} className="w-full h-[450px]" />
    </div>
  )
}
