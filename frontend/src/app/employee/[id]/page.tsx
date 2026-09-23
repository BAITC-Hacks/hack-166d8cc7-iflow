'use client';
import { use } from 'react';
import ConnectedCareerApp from '@/components/connected-career-app';
export default function EmployeePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ConnectedCareerApp requestedEmployee={id}/>;
}
