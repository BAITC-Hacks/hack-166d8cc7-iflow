type ArtKind = 'blocks' | 'people' | 'code' | 'book' | 'cup' | 'bag' | 'ticket';

export function Scene({ className = '' }: { className?: string }) {
  return <svg className={className} viewBox="0 0 620 340" fill="none" aria-hidden="true">
    <defs>
      <linearGradient id="hill" x1="340" y1="50" x2="480" y2="340" gradientUnits="userSpaceOnUse"><stop stopColor="#27886D"/><stop offset="1" stopColor="#125B4D"/></linearGradient>
      <linearGradient id="platform" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#ECF1A6"/><stop offset="1" stopColor="#CBDC71"/></linearGradient>
      <pattern id="terrain" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r="1" fill="#FFF" opacity=".13"/></pattern>
    </defs>
    <path d="M88 338C94 249 161 239 201 181C251 105 242 48 345 61C448 74 440 160 521 176C581 188 615 212 651 255V360Z" fill="url(#hill)"/>
    <path d="M66 311C117 246 143 277 200 204C276 106 253 24 367 43C470 60 452 146 531 166C598 183 639 196 664 264" stroke="#65A387" strokeOpacity=".25"/>
    <path d="M42 322C80 238 137 252 180 196C245 111 246 2 373 22C486 40 469 137 541 150C612 163 654 191 681 254" stroke="#65A387" strokeOpacity=".2"/>
    <path d="M129 338C133 275 174 274 222 221C298 138 269 96 349 102C429 108 430 182 504 203C576 223 593 248 619 292" stroke="#74B597" strokeOpacity=".22"/>
    <path d="M0 0H620V340H0Z" fill="url(#terrain)"/>
    <circle cx="486" cy="56" r="26" fill="#E4EC9B"/>
    <path d="M180 334C182 273 333 302 361 247C389 192 202 218 240 151C265 109 398 145 423 84" stroke="#0F483D" strokeWidth="20" strokeLinecap="round"/>
    <path d="M180 328C182 267 333 296 361 241C389 186 202 212 240 145C265 103 398 139 423 78" stroke="#83AB85" strokeWidth="12" strokeLinecap="round"/>
    <path d="M180 328C182 267 333 296 361 241C389 186 202 212 240 145C265 103 398 139 423 78" stroke="#DAE8AD" strokeWidth="2" strokeDasharray="4 9" strokeLinecap="round"/>
    <ellipse cx="342" cy="247" rx="57" ry="24" fill="#0B463B" opacity=".6"/>
    <path d="M289 221L342 192L395 221V236L342 267L289 236Z" fill="#B5C360"/>
    <path d="M289 221L342 191L395 221L342 252Z" fill="url(#platform)"/>
    <path d="M342 252V267" stroke="#91A341"/>
    <path d="M331 224L340 229L355 214" stroke="#125D47" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
    <ellipse cx="240" cy="163" rx="48" ry="17" fill="#0B463B" opacity=".5"/>
    <path d="M196 139L240 114L284 139V151L240 177L196 151Z" fill="#CCA642"/>
    <path d="M196 139L240 113L284 139L240 165Z" fill="#F8D36A"/>
    <path d="M226 137L240 129L254 137L240 145Z" fill="#FCEDBC"/>
    <path d="M240 130V104" stroke="#F8D36A" strokeWidth="3"/>
    <circle cx="240" cy="88" r="18" fill="#FEFBE6"/>
    <path d="M240 77L243 85L252 87L245 92L245 101L240 97L233 101L234 92L228 87L237 85Z" fill="#C69127"/>
    <ellipse cx="422" cy="87" rx="40" ry="16" fill="#0B463B" opacity=".5"/>
    <path d="M383 70L422 47L461 70V82L422 105L383 82Z" fill="#78A58A"/>
    <path d="M383 70L422 47L461 70L422 93Z" fill="#BBD6A8"/>
    <path d="M422 65V16" stroke="#F3F0CE" strokeWidth="3" strokeLinecap="round"/>
    <path d="M424 17C439 9 445 29 464 17V40C445 52 439 31 424 40Z" fill="#F8CE60"/>
    <g fill="#79AE7C"><path d="M154 194L169 152L184 194Z"/><path d="M145 205L169 168L193 205Z"/><path d="M474 287L487 255L500 287Z"/><path d="M468 298L487 267L506 298Z"/></g>
    <g stroke="#C6D99D" strokeWidth="3"><path d="M169 205V216"/><path d="M487 297V309"/></g>
    <g fill="#E5EBB9"><circle cx="289" cy="77" r="3"/><circle cx="445" cy="196" r="3"/><circle cx="553" cy="239" r="2"/></g>
    <path d="M542 111V123M536 117H548M191 85V93M187 89H195" stroke="#C6DAA7" strokeWidth="2" strokeLinecap="round"/>
    <g className="scene-caption" transform="translate(388 280) rotate(-8)"><rect width="151" height="34" rx="17" fill="#F6F4DD"/><circle cx="20" cy="17" r="5" fill="#087E68"/><text x="34" y="22" fill="#225645" fontSize="11" fontFamily="Arial, sans-serif" fontWeight="700">ТВОЙ ПУТЬ — ТВОЙ ТЕМП</text></g>
  </svg>;
}

export function Art({ kind, className = '' }: { kind: ArtKind; className?: string }) {
  return <svg viewBox="0 0 320 180" className={`object-art ${className}`} fill="none" aria-hidden="true">
    <ellipse cx="163" cy="155" rx="79" ry="10" fill="currentColor" opacity=".07"/>
    <circle cx="248" cy="44" r="26" stroke="currentColor" strokeOpacity=".09"/><circle cx="73" cy="118" r="35" stroke="currentColor" strokeOpacity=".09"/>
    <path d="M65 42V54M59 48H71M253 121V133M247 127H259" stroke="currentColor" strokeWidth="2" opacity=".3"/>
    {kind === 'blocks' && <>
      <path d="M96 110L139 86L182 110V141L139 166L96 141Z" fill="#168B70"/><path d="M96 110L139 85L182 110L139 136Z" fill="#A6D2A3"/><path d="M139 136V166" stroke="#076A54"/>
      <path d="M156 75L199 51L242 75V112L199 137L156 112Z" fill="#D1AB37"/><path d="M156 75L199 50L242 75L199 100Z" fill="#F5D86D"/><path d="M199 100V137" stroke="#B68E21"/>
      <path d="M110 46L150 23L190 46V80L150 104L110 80Z" fill="#126C5B"/><path d="M110 46L150 23L190 46L150 70Z" fill="#3F9C7D"/><path d="M150 70V104" stroke="#084E41"/>
      <path d="M165 13L170 7M208 32L216 28M89 64H79" stroke="#43856A" strokeWidth="2" strokeLinecap="round"/>
    </>}
    {kind === 'people' && <>
      <path d="M99 147C91 98 119 84 141 93C159 100 159 124 154 147Z" fill="#216F60"/><circle cx="127" cy="71" r="20" fill="#C78353"/><path d="M108 70C98 41 149 36 147 72L140 58L113 58Z" fill="#34342B"/>
      <path d="M170 148C167 104 181 88 204 96C227 104 230 132 225 148Z" fill="#D7B34D"/><circle cx="197" cy="74" r="20" fill="#DBA77B"/><path d="M177 68C174 36 225 46 216 85L208 72L209 61L177 69Z" fill="#4D392D"/>
      <path d="M136 116L168 123L184 112" stroke="#C78353" strokeWidth="12" strokeLinecap="round"/><path d="M156 115H168V128H156Z" fill="#FDF8EA"/><path d="M168 117C178 115 178 126 168 124" stroke="#FDF8EA" strokeWidth="3"/>
      <rect x="153" y="19" width="42" height="26" rx="13" fill="#FFF9E9"/><path d="M161 42L158 50L174 44" fill="#FFF9E9"/><circle cx="165" cy="32" r="2" fill="#AD7757"/><circle cx="175" cy="32" r="2" fill="#AD7757"/><circle cx="185" cy="32" r="2" fill="#AD7757"/>
    </>}
    {kind === 'code' && <g transform="rotate(-7 160 90)"><rect x="89" y="30" width="149" height="105" rx="10" fill="#3F4566"/><rect x="98" y="40" width="131" height="83" rx="4" fill="#FBF9FF"/><path d="M76 139H248L231 152H93Z" fill="#8284AA"/><path d="M139 141H188L183 146H143Z" fill="#BFC1D6"/><path d="M134 66L118 80L134 94M194 66L210 80L194 94M173 60L157 101" stroke="#8171B2" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round"/><path d="M219 15L227 8M250 52H261" stroke="#9385BD" strokeWidth="2"/></g>}
    {kind === 'book' && <g transform="rotate(-13 160 90)"><rect x="113" y="29" width="94" height="124" rx="5" fill="#B88541"/><path d="M118 147H204V155H118C111 155 109 147 118 147Z" fill="#FBF7E8"/><rect x="109" y="23" width="94" height="124" rx="5" fill="#EDD184"/><path d="M120 23V146" stroke="#CCA84D" strokeWidth="3"/><rect x="138" y="45" width="48" height="5" rx="2" fill="#71613D"/><rect x="138" y="56" width="34" height="4" rx="2" fill="#71613D"/><path d="M141 112L151 89L162 103L177 78L185 112Z" fill="#287D63"/><circle cx="144" cy="79" r="7" fill="#F9F2D8"/><path d="M180 23V43L174 38L168 43V23" fill="#217B63"/></g>}
    {kind === 'cup' && <g transform="rotate(9 160 90)"><path d="M125 50H196L187 150H135Z" fill="#117D66"/><path d="M196 67H208C229 67 224 112 191 111" stroke="#0B6552" strokeWidth="10"/><rect x="121" y="39" width="80" height="17" rx="7" fill="#224F43"/><rect x="127" y="33" width="66" height="10" rx="4" fill="#387763"/><path d="M149 84L161 74L173 86L161 100Z" fill="#F8CD4F"/><text x="140" y="118" fill="#F4F5D9" fontFamily="Arial" fontWeight="700" fontSize="16">halyk</text><path d="M143 19C139 10 148 11 143 2M163 19C159 10 168 11 163 2" stroke="#659880" strokeWidth="3" strokeLinecap="round"/></g>}
    {kind === 'bag' && <><path d="M108 61H211L221 151H98Z" fill="#D7CBE9"/><path d="M136 66V47C136 16 184 16 184 47V66" stroke="#66517E" strokeWidth="8"/><path d="M112 67H205L213 144H105Z" fill="#EDE4F5"/><path d="M143 98L160 82L178 99L160 117Z" fill="#208467"/><text x="136" y="135" fill="#3F6552" fontFamily="Arial" fontWeight="700" fontSize="18">halyk</text></>}
    {kind === 'ticket' && <g transform="rotate(-13 160 90)"><path d="M80 53H239V76C220 76 220 104 239 104V128H80V105C99 105 99 77 80 77Z" fill="#EFBC4C"/><path d="M195 54V128" stroke="#AD7D24" strokeWidth="2" strokeDasharray="4 5"/><text x="101" y="82" fill="#476045" fontFamily="Arial" fontWeight="900" fontSize="18">NEXT</text><text x="101" y="107" fill="#476045" fontFamily="Arial" fontWeight="900" fontSize="22">BIG IDEA</text><path d="M213 72V111M219 72V111" stroke="#856B31" strokeWidth="3"/></g>}
  </svg>;
}
