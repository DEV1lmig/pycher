import React from 'react';
import { Link } from '@tanstack/react-router';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <div className="container mx-auto px-4 py-12">
        <header className="text-center mb-16">
          <h1 className="text-5xl font-bold text-blue-900 mb-4">Welcome to Pycher</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Your interactive platform for learning Python programming through hands-on exercises and real-time feedback.
          </p>
        </header>

        <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
          <div className="bg-white p-8 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-blue-800 mb-4">Learn Python</h2>
            <p className="text-gray-600 mb-6">
              Our structured modules take you from beginner to advanced concepts with interactive lessons and coding challenges.
            </p>
            <div className="flex justify-center">
              <Link
                to="/module/intro"
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-md transition-colors"
              >
                Start Learning
              </Link>
            </div>
          </div>

          <div className="bg-white p-8 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-blue-800 mb-4">Try the Demo</h2>
            <p className="text-gray-600 mb-6">
              Not ready to commit? Try our interactive coding environment with a sample exercise to see how Pycher works.
            </p>
            <div className="flex justify-center">
              <Link
                to="/demo"
                className="bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-md transition-colors"
              >
                Launch Demo
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold text-blue-900 mb-6">Why Choose Pycher?</h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="p-4">
              <div className="text-blue-500 text-4xl mb-2">✓</div>
              <h3 className="text-lg font-semibold mb-2">Interactive Learning</h3>
              <p className="text-gray-600">Write, run, and test code directly in your browser</p>
            </div>
            <div className="p-4">
              <div className="text-blue-500 text-4xl mb-2">✓</div>
              <h3 className="text-lg font-semibold mb-2">AI-Powered Assistance</h3>
              <p className="text-gray-600">Get personalized hints and code explanations</p>
            </div>
            <div className="p-4">
              <div className="text-blue-500 text-4xl mb-2">✓</div>
              <h3 className="text-lg font-semibold mb-2">Track Your Progress</h3>
              <p className="text-gray-600">See your advancement through modules and exercises</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
