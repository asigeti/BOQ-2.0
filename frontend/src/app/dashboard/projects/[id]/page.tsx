import { Suspense } from 'react';
import ProjectClient from './ProjectClient';

export async function generateStaticParams() {
  return [{ id: '_' }];
}

export default function Page() {
  return (
    <Suspense>
      <ProjectClient />
    </Suspense>
  );
}
