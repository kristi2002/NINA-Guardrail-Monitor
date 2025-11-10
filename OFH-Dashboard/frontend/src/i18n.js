import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import en from './translations/en.json'
import it from './translations/it.json'

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      it: { translation: it }
    },
    fallbackLng: 'en',
    supportedLngs: ['en', 'it'],
    defaultNS: 'translation',
    ns: ['translation'],
    returnNull: false,
    debug: import.meta.env.DEV,
    detection: {
      order: ['querystring', 'localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupQuerystring: 'lng',
      convertDetectedLanguage: (lng) => lng?.split('-')[0],
      checkWhitelist: true
    },
    nonExplicitSupportedLngs: true,
    load: 'currentOnly',
    interpolation: {
      escapeValue: false
    },
    react: {
      useSuspense: false
    }
  })

export default i18n

