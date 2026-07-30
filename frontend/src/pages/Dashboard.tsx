import { useAuthStore } from '@/store/authStore'
import InstructorDashboard from '@/components/dashboards/InstructorDashboard'
import StudentDashboard from '@/components/dashboards/StudentDashboard'

export default function Dashboard() {
  const user = useAuthStore((state) => state.user)

  if (!user) {
    return <div className="p-6 text-white">Loading...</div>
  }

  if (user.role === 'student') {
    return <StudentDashboard />
  }

  // Admin or Instructor
  return <InstructorDashboard />
}
