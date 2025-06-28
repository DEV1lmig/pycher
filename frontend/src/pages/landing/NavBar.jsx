import logo from '../../assets/img/logo-pycher.png';
import { Link } from '@tanstack/react-router';
import FadeContent from '../../components/ui/fade-content';

export default function NavBar() {
    return (
        <div className="fixed top-0 left-0 w-full px-12 py-4 bg-dark bg-opacity-50 backdrop-blur-lg text-white z-50">
            <FadeContent blur={true} duration={1200} easing="ease-out" initialOpacity={0}>
            <div className="flex flex-row items-center justify-between w-full">
                <img src={logo} alt="logo" className="w-48 h-auto cursor-pointer" />
                <div className="flex flex-row items-center space-x-4">
                    <Link to="/login" className="px-4 py-2 text-base font-semibold text-white  hover:text-primary-light">Inicio de sesión</Link>
                    <Link to="/register" className="px-4 py-2 text-base font-semibold text-white  rounded hover:text-secondary">Registro</Link>
                </div>
            </div>
            </FadeContent>
        </div>

    );
}
