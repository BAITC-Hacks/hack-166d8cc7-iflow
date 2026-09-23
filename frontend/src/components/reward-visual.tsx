'use client';

import { useId } from 'react';

/** Quiet studio-style product illustrations for the rewards catalogue. */
export function RewardVisual({ kind, className = '' }: { kind: string; className?: string }) {
  const id = useId().replace(/:/g, '');
  const paint = (name: string) => `url(#${id}-${name})`;

  return (
    <svg className={`reward-product ${className}`} viewBox="0 0 400 280" fill="none" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id={`${id}-studio`} x1="200" y1="0" x2="200" y2="280" gradientUnits="userSpaceOnUse">
          <stop stopColor="#F4F3F0" /><stop offset="1" stopColor="#EAE8E3" />
        </linearGradient>
        <radialGradient id={`${id}-shadow`}>
          <stop stopColor="#242824" stopOpacity=".18" /><stop offset="1" stopColor="#242824" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`${id}-cover`} x1="127" y1="56" x2="270" y2="228" gradientUnits="userSpaceOnUse">
          <stop stopColor="#373B38" /><stop offset=".45" stopColor="#232A27" /><stop offset="1" stopColor="#18221E" />
        </linearGradient>
        <linearGradient id={`${id}-steel`} x1="153" y1="0" x2="247" y2="0" gradientUnits="userSpaceOnUse">
          <stop stopColor="#9FA5A1" /><stop offset=".23" stopColor="#F2F4F1" /><stop offset=".52" stopColor="#D8DEDA" /><stop offset=".79" stopColor="#8B948E" /><stop offset="1" stopColor="#C1C7C2" />
        </linearGradient>
        <linearGradient id={`${id}-ceramic`} x1="153" y1="0" x2="247" y2="0" gradientUnits="userSpaceOnUse">
          <stop stopColor="#D4D8D3" /><stop offset=".2" stopColor="#F7F8F4" /><stop offset=".43" stopColor="#FFFFFF" /><stop offset=".72" stopColor="#EFF1EB" /><stop offset="1" stopColor="#C7CFC7" />
        </linearGradient>
        <linearGradient id={`${id}-canvas`} x1="120" y1="134" x2="275" y2="205" gradientUnits="userSpaceOnUse">
          <stop stopColor="#D3C8B5" /><stop offset=".13" stopColor="#EEE8DB" /><stop offset=".5" stopColor="#F4EEDF" /><stop offset=".85" stopColor="#E8DFCE" /><stop offset="1" stopColor="#CFC1AB" />
        </linearGradient>
        <linearGradient id={`${id}-paper`} x1="85" y1="71" x2="320" y2="210" gradientUnits="userSpaceOnUse">
          <stop stopColor="#FFFEFA" /><stop offset="1" stopColor="#F0EDE4" />
        </linearGradient>
      </defs>

      <path d="M0 0H400V280H0Z" fill={paint('studio')} />

      {kind === 'book' && <>
        <ellipse cx="201" cy="239" rx="105" ry="16" fill={paint('shadow')} />
        <path d="M137 55L270 63V228L256 237L130 226Z" fill="#1B241E" />
        <path d="M137 210L265 217V229L254 233L137 222Z" fill="#DDDAD0" />
        <path d="M146 215L262 221M146 218L262 224M146 221L259 227" stroke="#BFBCAF" strokeWidth=".7" />
        <path d="M127 49L257 55C262 55 264 58 264 63V219L134 214C130 214 127 211 127 206Z" fill={paint('cover')} />
        <path d="M127 49C121 49 117 54 117 62V207C117 217 123 225 132 226L254 233V225L133 219C127 219 124 215 124 211C124 207 128 205 133 205L137 51Z" fill="#28312C" />
        <path d="M137 52V209" stroke="#536257" strokeOpacity=".6" />
        <path d="M141 52L256 58" stroke="#FFFFFF" strokeOpacity=".1" />
        <text x="156" y="89" fill="#A8C1AB" fontFamily="Arial, sans-serif" fontSize="21" fontWeight="600" letterSpacing="-.7">Halyk</text>
        <path d="M157 111H241" stroke="#9AAF9D" strokeOpacity=".28" />
        <text x="156" y="134" fill="#E3E5DC" fontFamily="Arial, sans-serif" fontSize="10" letterSpacing="2.4">IDEAS.</text>
        <text x="156" y="151" fill="#E3E5DC" fontFamily="Arial, sans-serif" fontSize="10" letterSpacing="2.4">IN PROGRESS.</text>
        <text x="157" y="190" fill="#8E9C91" fontFamily="Arial, sans-serif" fontSize="6" letterSpacing="1.4">CAREER COLLECTION</text>
        <path d="M233 218V237L229 234L225 237V218" fill="#32674D" />
      </>}

      {kind === 'cup' && <>
        <ellipse cx="204" cy="238" rx="74" ry="14" fill={paint('shadow')} />
        <path d="M153 76H247L237 217C236 229 164 229 163 217Z" fill={paint('steel')} />
        <path d="M154 87H246L237 210C234 222 165 222 163 210Z" fill={paint('ceramic')} />
        <ellipse cx="200" cy="77" rx="47" ry="7" fill="#404A43" />
        <path d="M151 70C151 63 249 63 249 70V80C249 86 151 86 151 80Z" fill="#303B33" />
        <ellipse cx="200" cy="69" rx="49" ry="8" fill="#566057" />
        <ellipse cx="200" cy="67" rx="42" ry="5" fill="#333D35" />
        <rect x="176" y="61" width="48" height="7" rx="3.5" fill="#626E63" />
        <path d="M162 92L170 199" stroke="#FFFFFF" strokeOpacity=".6" strokeWidth="2" />
        <text x="177" y="150" fill="#366447" fontFamily="Arial, sans-serif" fontSize="18" fontWeight="600" letterSpacing="-.7">Halyk</text>
        <text x="180" y="164" fill="#798478" fontFamily="Arial, sans-serif" fontSize="5" letterSpacing="1.2">EVERYDAY ESSENTIALS</text>
        <path d="M165 218C181 223 217 223 235 218" stroke="#8C978E" strokeOpacity=".7" />
      </>}

      {kind === 'bag' && <>
        <ellipse cx="200" cy="245" rx="104" ry="16" fill={paint('shadow')} />
        <path d="M145 117V75C145 33 241 34 241 75V117" stroke="#BFB39D" strokeWidth="11" />
        <path d="M153 114V77C153 45 233 44 233 77V114" stroke="#E5DDCD" strokeWidth="7" />
        <path d="M121 100L274 101L280 228Q250 250 129 236L119 224Z" fill="#CDBFA7" />
        <path d="M123 98H270L266 231Q193 243 121 230Z" fill={paint('canvas')} />
        <path d="M127 103H266M130 108H264" stroke="#B9AA91" strokeWidth=".7" />
        <path d="M151 115V75C151 35 239 35 239 75V115" stroke="#EAE3D5" strokeWidth="10" />
        <path d="M149 113V75C149 34 241 34 241 75V113" stroke="#C4B69F" strokeWidth=".65" />
        <path d="M154 113V75C154 43 236 43 236 75V113" stroke="#FFFBF1" strokeWidth=".8" />
        <path d="M149 106V119H156V106M234 106V119H241V106" stroke="#B7A990" strokeWidth=".8" />
        <path d="M129 115L127 227M261 115L260 229" stroke="#BCAF97" strokeWidth=".8" strokeDasharray="2 3" />
        <path d="M137 225C165 231 228 233 253 225" stroke="#C5B79F" strokeOpacity=".5" />
        <text x="165" y="168" fill="#345B42" fontFamily="Arial, sans-serif" fontSize="28" fontWeight="600" letterSpacing="-1.1">Halyk</text>
        <text x="165" y="185" fill="#74816F" fontFamily="Arial, sans-serif" fontSize="5.7" letterSpacing="1.5">GOOD THINGS. EVERY DAY.</text>
      </>}

      {kind === 'ticket' && <>
        <ellipse cx="200" cy="209" rx="151" ry="23" fill={paint('shadow')} />
        <path d="M62 83H338V126C328 126 328 145 338 145V191H62V145C72 145 72 126 62 126Z" fill="#D5D1C7" />
        <path d="M60 78H336V122C325 122 325 140 336 140V186H60V140C71 140 71 122 60 122Z" fill={paint('paper')} stroke="#D7D3C8" strokeWidth=".8" />
        <path d="M60 78H71V186H60V140C71 140 71 122 60 122Z" fill="#244E36" />
        <path d="M268 79V185" stroke="#B8B6AC" strokeWidth=".8" strokeDasharray="2 3" />
        <text x="86" y="103" fill="#4C6251" fontFamily="Arial, sans-serif" fontSize="9" fontWeight="600">Halyk</text>
        <text x="86" y="129" fill="#272F29" fontFamily="Arial, sans-serif" fontSize="19" fontWeight="600" letterSpacing="-.6">Ideas worth</text>
        <text x="86" y="150" fill="#272F29" fontFamily="Arial, sans-serif" fontSize="19" fontWeight="600" letterSpacing="-.6">meeting.</text>
        <path d="M86 164H248" stroke="#D7D7CA" strokeWidth=".7" />
        <text x="87" y="175" fill="#7F867A" fontFamily="Arial, sans-serif" fontSize="5.3" letterSpacing="1.2">COMMUNITY · CONNECTIONS · GROWTH</text>
        <text x="283" y="102" fill="#6D776B" fontFamily="Arial, sans-serif" fontSize="6" letterSpacing="1.2">ADMIT ONE</text>
        <text x="281" y="133" fill="#2D5038" fontFamily="Arial, sans-serif" fontSize="27" fontWeight="500" letterSpacing="-1">01</text>
        <g fill="#3A443B">
          <path d="M282 146H284V170H282ZM287 146H288V170H287ZM291 146H294V170H291ZM297 146H298V170H297ZM301 146H303V170H301ZM306 146H307V170H306ZM310 146H313V170H310ZM316 146H317V170H316ZM320 146H322V170H320Z" />
        </g>
      </>}

      {!['book', 'cup', 'bag', 'ticket'].includes(kind) && <>
        <ellipse cx="200" cy="226" rx="94" ry="17" fill={paint('shadow')} />
        <rect x="125" y="77" width="150" height="138" rx="2" fill="#DCD6C9" />
        <path d="M125 77H275V88H125Z" fill="#E8E3D8" />
        <path d="M191 77H209V215H191Z" fill="#35553E" />
        <rect x="224" y="103" width="37" height="16" fill="#F3F0E8" />
        <text x="229" y="114" fill="#3C5641" fontFamily="Arial, sans-serif" fontSize="9" fontWeight="600">Halyk</text>
      </>}
    </svg>
  );
}
