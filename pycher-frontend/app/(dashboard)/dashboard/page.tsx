"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { BookOpen, Settings, FileText, GraduationCap } from "lucide-react";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";

export default function Dashboard() {
  const [selectedCourse, setSelectedCourse] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState('courses');

  const navigation = [
    { name: 'Courses', href: '#', icon: GraduationCap, id: 'courses' },
    { name: 'Books', href: '#', icon: BookOpen, id: 'books' },
    { name: 'Reports', href: '#', icon: FileText, id: 'reports' },
    { name: 'Settings', href: '#', icon: Settings, id: 'settings' },
  ];

  const courses = [
    {
      id: 1,
      title: 'Basic concepts',
      description: 'Basic concepts for Python programming languages',
      image: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?auto=format&fit=crop&q=80&w=500',
      classes: [
        {
          id: 1,
          title: 'Variables',
          description: 'A class about python variables',
          image: 'https://images.unsplash.com/photo-1516116216624-53e697fedbea?auto=format&fit=crop&q=80&w=500',
        },
        {
          id: 2,
          title: 'Data Types',
          description: 'Understanding Python data types',
          image: 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=500',
        },
      ],
    },
    {
      id: 2,
      title: 'Basic Programming',
      description: 'Basic programmig for Python programming languages',
      image: 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=500',
      classes: [
        {
          id: 3,
          title: 'Control Flow',
          description: 'Learn about if statements and loops',
          image: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&q=80&w=500',
        },
      ],
    },
    {
      id: 3,
      title: 'Advanced Python',
      description: 'Advanced concepts and programming techniques',
      image: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&q=80&w=500',
      classes: [],
    },
  ];

  const books = [
    {
      id: 1,
      title: 'React Rendezvous',
      author: 'Ethan Byte',
      image: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&q=80&w=1000',
    },
    {
      id: 2,
      title: 'Async Awakenings',
      author: 'Nina Netcode',
      image: 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?auto=format&fit=crop&q=80&w=1000',
    },
    {
      id: 3,
      title: 'The Art of Reusability',
      author: 'Lena Logic',
      image: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&q=80&w=1000',
    },
    {
      id: 4,
      title: 'Stateful Symphony',
      author: 'Beth Binary',
      image: 'https://images.unsplash.com/photo-1516116216624-53e697fedbea?auto=format&fit=crop&q=80&w=1000',
    },
  ];

  const selectedCourseData = courses.find(course => course.id === selectedCourse);

  return (
    <div className="min-h-screen bg-base">
      <div className="flex h-16 items-center px-4 border-b">
        <div className="flex items-center gap-2">
          <span className="font-gelasio text-2xl font-bold">
            <span className="text-primary">Py</span>
            <span>Cher</span>
          </span>
        </div>
        <nav className="flex items-center space-x-4 lg:space-x-6 mx-6">
          {navigation.map((item) => (
            <Button
              key={item.name}
              variant={activeTab === item.id ? "default" : "ghost"}
              className="text-sm font-medium transition-colors"
              onClick={() => setActiveTab(item.id)}
            >
              <item.icon className="h-4 w-4 mr-2" />
              {item.name}
            </Button>
          ))}
        </nav>
        <div className="ml-auto flex items-center space-x-4">
          <Avatar>
            <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" />
            <AvatarFallback>CN</AvatarFallback>
          </Avatar>
        </div>
      </div>
      <main className="container mx-auto py-8">
        {activeTab === 'courses' ? (
          <div className="space-y-8">
            <section>
              <h2 className="text-3xl font-bold mb-6">Courses</h2>
              <Carousel className="w-full">
                <CarouselContent className="-ml-2 md:-ml-4">
                  {courses.map((course) => (
                    <CarouselItem key={course.id} className="pl-2 md:pl-4 md:basis-1/2 lg:basis-1/3">
                      <Card
                        className="flex flex-row overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary transition-all"
                        onClick={() => setSelectedCourse(course.id)}
                      >
                        <div className="w-1/3">
                          <img
                            src={course.image}
                            alt={course.title}
                            className="object-cover w-full h-full"
                          />
                        </div>
                        <div className="w-2/3 p-4">
                          <h3 className="text-xl font-semibold mb-2">{course.title}</h3>
                          <p className="text-muted-foreground text-sm">{course.description}</p>
                        </div>
                      </Card>
                    </CarouselItem>
                  ))}
                </CarouselContent>
                <CarouselPrevious />
                <CarouselNext />
              </Carousel>
            </section>

            <section>
              <h2 className="text-3xl font-bold mb-6">Classes</h2>
              {selectedCourseData ? (
                selectedCourseData.classes.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4">
                    {selectedCourseData.classes.map((class_) => (
                      <Card key={class_.id} className="flex flex-row overflow-hidden">
                        <div className="w-1/3">
                          <img
                            src={class_.image}
                            alt={class_.title}
                            className="object-cover w-full h-full"
                          />
                        </div>
                        <div className="w-2/3 p-4">
                          <h3 className="text-xl font-semibold mb-2">{class_.title}</h3>
                          <p className="text-muted-foreground">{class_.description}</p>
                        </div>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <Card className="p-8 text-center">
                    <p className="text-muted-foreground">No classes available for this course yet.</p>
                  </Card>
                )
              ) : (
                <Card className="p-8 text-center">
                  <p className="text-muted-foreground">Select a course to view its classes.</p>
                </Card>
              )}
            </section>
          </div>
        ) : activeTab === 'books' ? (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-bold">Books</h2>
                <p className="text-muted-foreground mt-1">
                  A collection of books that can help you understand the language better.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {books.map((book) => (
                <Card key={book.id} className="overflow-hidden hover:ring-2 hover:ring-primary transition-all cursor-pointer">
                  <div className="aspect-[3/4] relative">
                    <img
                      src={book.image}
                      alt={book.title}
                      className="object-cover w-full h-full"
                    />
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold text-lg mb-1">{book.title}</h3>
                    <p className="text-muted-foreground text-sm">{book.author}</p>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
            <Card className="p-8 text-center">
              <p className="text-muted-foreground">This section is under development.</p>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
