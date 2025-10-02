const Spinner = ({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) => {
    const sizes = {
      sm: 'w-4 h-4',
      md: 'w-8 h-8',
      lg: 'w-12 h-12',
    };
  
    return (
      <div className={`${sizes[size]} border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin`} />
    );
  };
  
  export default Spinner;