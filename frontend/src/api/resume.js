// frontend/src/api/resume.js
// Resume API — wraps all /api/v1/resumes/* endpoints.
// Assumes a pre-configured axios instance is exported from '@/api/index.js'
// with baseURL already set and the JWT token injected via a request interceptor.

import request from '@/utils/request'

/**
 * List all resumes for the current user (no content payload).
 * @returns {Promise<Array>} array of resume metadata objects
 */
export function listResumes() {
  return request({ url: '/resumes', method: 'get' })
}

/**
 * Fetch the current user's main resume (with full content).
 * @returns {Promise<Object>}
 */
export function getMainResume() {
  return request({ url: '/resumes/main', method: 'get' })
}

/**
 * Fetch a single resume by id (with full content).
 * @param {number} id
 * @returns {Promise<Object>}
 */
export function getResume(id) {
  return request({ url: `/resumes/${id}`, method: 'get' })
}

/**
 * Create a new resume.
 * @param {Object} payload
 * @param {string}  payload.title
 * @param {boolean} payload.isMain
 * @param {number}  [payload.jobId]
 * @param {Object}  [payload.content]
 * @returns {Promise<Object>} created resume
 */
export function createResume(payload) {
  return request({ url: '/resumes', method: 'post', data: payload })
}

/**
 * Update a resume's title and/or content.
 * @param {number} id
 * @param {Object} payload  { title?, content? }
 * @returns {Promise<Object>} updated resume
 */
export function updateResume(id, payload) {
  return request({ url: `/resumes/${id}`, method: 'put', data: payload })
}

/**
 * Delete a customized resume.
 * @param {number} id
 * @returns {Promise<void>}
 */
export function deleteResume(id) {
  return request({ url: `/resumes/${id}`, method: 'delete' })
}

/**
 * Overwrite a customized resume's content with the main resume's content.
 * @param {number} id  target resume id
 * @returns {Promise<Object>} updated resume
 */
export function copyFromMain(id) {
  return request({ url: `/resumes/${id}/copy-from-main`, method: 'post' })
}