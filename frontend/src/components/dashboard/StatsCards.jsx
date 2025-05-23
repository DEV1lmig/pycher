import { BookOpen, Code, Clock } from "lucide-react"
import AnimatedContent from '../ui/animated-content'

export function StatsCards() {
  const stats = [
    {
      title: "Cursos Activos",
      value: "3",
      icon: BookOpen,
      color: "bg-[#5f2dee]/10 text-primary",
    },
    {
      title: "Ejercicios Completados",
      value: "42",
      icon: Code,
      color: "bg-[#f2d231]/10 text-[#f2d231]",
    },
    {
      title: "Horas de Estudio",
      value: "28",
      icon: Clock,
      color: "bg-[#5f2dee]/10 text-[#9980f2]",
    },
  ]

  const bgColors = [
  "bg-[#5f2dee]/10",
  "bg-[#f2d231]/10",
  "bg-[#9980f2]/20"
];


  return (
    <AnimatedContent
          distance={40}
          direction="vertical"
          reverse={true}
          config={{ tension: 100, friction: 10 }}
          initialOpacity={0}
          animateOpacity
          scale={1}
          threshold={0.2}
          delay={100}
        >
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {stats.map((stat, index) => (
        <div
          key={index}
          className={`rounded-lg p-4 hover:scale-105 transition-transform duration-300 ${bgColors[index % bgColors.length]}`}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-400 text-sm">{stat.title}</p>
              <p className="text-2xl font-bold mt-1">{stat.value}</p>
            </div>
            <div className={`p-2 rounded-md ${stat.color}`}>
              <stat.icon className="h-5 w-5" />
            </div>
          </div>
        </div>
      ))}
    </div>
    </AnimatedContent>
  )
}
