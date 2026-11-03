import FilingDetail from '../../workspace/FilingDetail';export default async function Page({params}:{params:Promise<{filingId:string}>}){return <FilingDetail id={(await params).filingId}/>}
