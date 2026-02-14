import PlanClient from './PlanClient';

export async function generateStaticParams() {
  return [{ id: '_' }];
}

export default function Page() {
  return <PlanClient />;
}
