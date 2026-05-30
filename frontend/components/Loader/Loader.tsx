import { Oval } from "react-loader-spinner";

export default function Loader() {
  return (
    <Oval
      height={300}
      width={300}
      color="#4fa94d"
      wrapperStyle={{}}
      wrapperClass=""
      visible={true}
      ariaLabel='oval-loading'
      secondaryColor="#f97316"
      strokeWidth={2}
      strokeWidthSecondary={2}
    />
  )
}