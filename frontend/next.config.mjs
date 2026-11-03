const config = {
  logging:false,
  async rewrites() {
    const base = (process.env.FINN_BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
    return [{source:'/api/:path*', destination:`${base}/api/:path*`}, {source:'/backend-health', destination:`${base}/health`}];
  },
  poweredByHeader:false,
  async headers() {
    const connection=new URL(process.env.NEXT_PUBLIC_API_BASE || 'http://localhost').origin;
    const connect=process.env.NEXT_PUBLIC_API_BASE?`'self' ${connection}`:"'self'";
    const scripts=process.env.NODE_ENV==='development'?"'self' 'unsafe-inline' 'unsafe-eval'":"'self' 'unsafe-inline'";
    return [{source:'/(.*)',headers:[
      {key:'X-Content-Type-Options',value:'nosniff'},
      {key:'Referrer-Policy',value:'no-referrer'},
      {key:'X-Frame-Options',value:'SAMEORIGIN'},
      {key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=(), payment=()'},
      {key:'Content-Security-Policy',value:`default-src 'self'; script-src ${scripts}; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data: blob:; connect-src ${connect}; frame-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'`}
    ]}];
  }
};
export default config;
