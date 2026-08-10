/*********************************************************************
 *
 * Software License Agreement (BSD License)
 *
 *  Copyright (c) 2015-2016, Jiri Horner.
 *  All rights reserved.
 *
 *  Redistribution and use in source and binary forms, with or without
 *  modification, are permitted provided that the following conditions
 *  are met:
 *
 *   * Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *   * Redistributions in binary form must reproduce the above
 *     copyright notice, this list of conditions and the following
 *     disclaimer in the documentation and/or other materials provided
 *     with the distribution.
 *   * Neither the name of the Jiri Horner nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 *  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 *  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 *  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 *  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 *  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 *  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 *  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 *  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 *  POSSIBILITY OF SUCH DAMAGE.
 *
 *********************************************************************/

#include <combine_grids/grid_compositor.h>
#include <combine_grids/grid_warper.h>
#include <combine_grids/merging_pipeline.h>
#include <ros/assert.h>
#include <ros/console.h>

#include <limits>
#include <opencv2/stitching/detail/matchers.hpp>
#include <opencv2/stitching/detail/motion_estimators.hpp>
#include <opencv2/stitching/detail/util.hpp>

#include "estimation_internal.h"

namespace combine_grids
{
bool MergingPipeline::estimateTransforms(FeatureType feature_type,
                                         double confidence)
{
  transforms_use_meters_ = false;
  std::vector<cv::detail::ImageFeatures> image_features;
  std::vector<cv::detail::MatchesInfo> pairwise_matches;
  std::vector<cv::detail::CameraParams> transforms;
  std::vector<int> good_indices;
  // TODO investigate value translation effect on features
  auto finder = internal::chooseFeatureFinder(feature_type);
  cv::Ptr<cv::detail::FeaturesMatcher> matcher =
      cv::makePtr<cv::detail::AffineBestOf2NearestMatcher>();
  cv::Ptr<cv::detail::Estimator> estimator =
      cv::makePtr<cv::detail::AffineBasedEstimator>();
  cv::Ptr<cv::detail::BundleAdjusterBase> adjuster =
      cv::makePtr<cv::detail::BundleAdjusterAffinePartial>();

  if (images_.empty()) {
    return true;
  }

  /* find features in images */
  ROS_DEBUG("computing features");
  image_features.reserve(images_.size());
  for (const cv::Mat& image : images_) {
    image_features.emplace_back();
    if (!image.empty()) {
#if CV_VERSION_MAJOR >= 4
      cv::detail::computeImageFeatures(finder, image, image_features.back());
#else
      (*finder)(image, image_features.back());
#endif
    }
  }
  finder = {};

  /* find corespondent features */
  ROS_DEBUG("pairwise matching features");
  (*matcher)(image_features, pairwise_matches);
  matcher = {};

#ifndef NDEBUG
  internal::writeDebugMatchingInfo(images_, image_features, pairwise_matches);
#endif

  /* use only matches that has enough confidence. leave out matches that are not
   * connected (small components) */
  good_indices = cv::detail::leaveBiggestComponent(
      image_features, pairwise_matches, static_cast<float>(confidence));

  // no match found. try set first non-empty grid as reference frame. we try to
  // avoid setting empty grid as reference frame, in case some maps never
  // arrive. If all is empty just set null transforms.
  if (good_indices.size() == 1) {
    transforms_.clear();
    transforms_.resize(images_.size());
    for (size_t i = 0; i < images_.size(); ++i) {
      if (!images_[i].empty()) {
        // set identity
        transforms_[i] = cv::Mat::eye(3, 3, CV_64F);
        break;
      }
    }
    return true;
  }

  /* estimate transform */
  ROS_DEBUG("calculating transforms in global reference frame");
  // note: currently used estimator never fails
  if (!(*estimator)(image_features, pairwise_matches, transforms)) {
    return false;
  }

  /* levmarq optimization */
  // openCV just accepts float transforms
  for (auto& transform : transforms) {
    transform.R.convertTo(transform.R, CV_32F);
  }
  ROS_DEBUG("optimizing global transforms");
  adjuster->setConfThresh(confidence);
  if (!(*adjuster)(image_features, pairwise_matches, transforms)) {
    ROS_WARN("Bundle adjusting failed. Could not estimate transforms.");
    return false;
  }

  transforms_.clear();
  transforms_.resize(images_.size());
  size_t i = 0;
  for (auto& j : good_indices) {
    // we want to work with transforms as doubles
    transforms[i].R.convertTo(transforms_[static_cast<size_t>(j)], CV_64F);
    ++i;
  }

  return true;
}

// checks whether given matrix is an identity, i.e. exactly appropriate Mat::eye
static inline bool isIdentity(const cv::Mat& matrix)
{
  if (matrix.empty()) {
    return false;
  }
  cv::MatExpr diff = matrix != cv::Mat::eye(matrix.size(), matrix.type());
  return cv::countNonZero(diff) == 0;
}

/* Place grid in merge canvas using init_pose + OccupancyGrid.info.origin (meters). */
static cv::Mat warpTransformForGrid(const cv::Mat& transform,
                                    const nav_msgs::OccupancyGridConstPtr& grid,
                                    bool transforms_use_meters, double min_x,
                                    double min_y)
{
  if (transform.empty() || !grid || grid->info.resolution <= 0.f) {
    return transform;
  }
  cv::Mat out = transform.clone();
  const double res = static_cast<double>(grid->info.resolution);
  if (transforms_use_meters) {
    const double tx = out.at<double>(0, 2);
    const double ty = out.at<double>(1, 2);
    const double ox = grid->info.origin.position.x;
    const double oy = grid->info.origin.position.y;
    out.at<double>(0, 2) = (tx + ox - min_x) / res;
    out.at<double>(1, 2) = (ty + oy - min_y) / res;
  }
  return out;
}

static bool computeWorldBounds(
    const std::vector<nav_msgs::OccupancyGridConstPtr>& grids,
    const std::vector<cv::Mat>& transforms, bool transforms_use_meters,
    double& min_x, double& min_y)
{
  min_x = std::numeric_limits<double>::infinity();
  min_y = std::numeric_limits<double>::infinity();
  size_t count = 0;
  for (size_t i = 0; i < grids.size(); ++i) {
    if (!grids[i] || grids[i]->data.empty() || transforms[i].empty()) {
      continue;
    }
    const double res = static_cast<double>(grids[i]->info.resolution);
    double tx = 0.0;
    double ty = 0.0;
    if (transforms_use_meters) {
      tx = transforms[i].at<double>(0, 2);
      ty = transforms[i].at<double>(1, 2);
    } else {
      tx = transforms[i].at<double>(0, 2) * res;
      ty = transforms[i].at<double>(1, 2) * res;
    }
    const double ox = grids[i]->info.origin.position.x;
    const double oy = grids[i]->info.origin.position.y;
    const double gw = grids[i]->info.width * res;
    const double gh = grids[i]->info.height * res;
    min_x = std::min({min_x, tx + ox, tx + ox + gw});
    min_y = std::min({min_y, ty + oy, ty + oy + gh});
    ++count;
  }
  return count > 0 && std::isfinite(min_x) && std::isfinite(min_y);
}

static inline bool isIdentityRotation(const cv::Mat& matrix)
{
  if (matrix.empty()) {
    return false;
  }
  return std::abs(matrix.at<double>(1, 0)) < 1e-9 &&
         std::abs(matrix.at<double>(0, 1)) < 1e-9;
}

/* Known init_pose path: copy cells by world (x,y), avoiding OpenCV warp Y quirks. */
static nav_msgs::OccupancyGrid::Ptr composeGridsWorldStamp(
    const std::vector<nav_msgs::OccupancyGridConstPtr>& grids,
    const std::vector<cv::Mat>& transforms)
{
  double min_x = std::numeric_limits<double>::infinity();
  double min_y = std::numeric_limits<double>::infinity();
  double max_x = -std::numeric_limits<double>::infinity();
  double max_y = -std::numeric_limits<double>::infinity();
  float res = 0.f;
  size_t valid = 0;

  for (size_t i = 0; i < grids.size(); ++i) {
    if (!grids[i] || grids[i]->data.empty() || transforms[i].empty()) {
      continue;
    }
    if (!isIdentityRotation(transforms[i])) {
      return nullptr;
    }
    const double tx = transforms[i].at<double>(0, 2);
    const double ty = transforms[i].at<double>(1, 2);
    const double ox = grids[i]->info.origin.position.x;
    const double oy = grids[i]->info.origin.position.y;
    const double r = static_cast<double>(grids[i]->info.resolution);
    const double gw = grids[i]->info.width * r;
    const double gh = grids[i]->info.height * r;
    min_x = std::min(min_x, tx + ox);
    min_y = std::min(min_y, ty + oy);
    max_x = std::max(max_x, tx + ox + gw);
    max_y = std::max(max_y, ty + oy + gh);
    res = grids[i]->info.resolution;
    ++valid;
  }

  if (valid == 0 || !std::isfinite(min_x) || res <= 0.f) {
    return nullptr;
  }

  if (valid == 1) {
    for (size_t i = 0; i < grids.size(); ++i) {
      if (!grids[i] || grids[i]->data.empty() || transforms[i].empty()) {
        continue;
      }
      nav_msgs::OccupancyGrid::Ptr result(new nav_msgs::OccupancyGrid(*grids[i]));
      result->info.origin.orientation.w = 1.0;
      result->info.origin.position.x += transforms[i].at<double>(0, 2);
      result->info.origin.position.y += transforms[i].at<double>(1, 2);
      return result;
    }
    return nullptr;
  }

  const double r = static_cast<double>(res);
  const uint32_t out_w =
      static_cast<uint32_t>(std::ceil((max_x - min_x) / r));
  const uint32_t out_h =
      static_cast<uint32_t>(std::ceil((max_y - min_y) / r));
  if (out_w == 0 || out_h == 0) {
    return nullptr;
  }

  nav_msgs::OccupancyGrid::Ptr result(new nav_msgs::OccupancyGrid());
  result->info.resolution = res;
  result->info.width = out_w;
  result->info.height = out_h;
  result->info.origin.position.x = min_x;
  result->info.origin.position.y = min_y;
  result->info.origin.orientation.w = 1.0;
  result->data.assign(static_cast<size_t>(out_w) * out_h, -1);

  for (size_t i = 0; i < grids.size(); ++i) {
    if (!grids[i] || grids[i]->data.empty() || transforms[i].empty()) {
      continue;
    }
    const double tx = transforms[i].at<double>(0, 2);
    const double ty = transforms[i].at<double>(1, 2);
    const double ox = grids[i]->info.origin.position.x;
    const double oy = grids[i]->info.origin.position.y;
    const uint32_t sw = grids[i]->info.width;
    const uint32_t sh = grids[i]->info.height;

    for (uint32_t my = 0; my < sh; ++my) {
      for (uint32_t mx = 0; mx < sw; ++mx) {
        const int8_t src = grids[i]->data[static_cast<size_t>(my) * sw + mx];
        if (src < 0) {
          continue;
        }
        const int out_mx =
            static_cast<int>(std::floor((tx + ox + mx * r - min_x) / r));
        const int out_my =
            static_cast<int>(std::floor((ty + oy + my * r - min_y) / r));
        if (out_mx < 0 || out_my < 0 ||
            out_mx >= static_cast<int>(out_w) ||
            out_my >= static_cast<int>(out_h)) {
          continue;
        }
        const size_t out_idx =
            static_cast<size_t>(out_my) * out_w + static_cast<size_t>(out_mx);
        result->data[out_idx] = std::max(result->data[out_idx], src);
      }
    }
  }

  ROS_DEBUG("world-stamp merged map origin=(%.3f, %.3f) size=%ux%u",
            result->info.origin.position.x, result->info.origin.position.y,
            result->info.width, result->info.height);
  return result;
}

nav_msgs::OccupancyGrid::Ptr MergingPipeline::composeGrids()
{
  ROS_ASSERT(images_.size() == transforms_.size());
  ROS_ASSERT(images_.size() == grids_.size());

  if (images_.empty()) {
    return nullptr;
  }

  /* Known init poses: stamp by world coordinates (RTAB/Create3 global grid origins). */
  if (transforms_use_meters_) {
    nav_msgs::OccupancyGrid::Ptr stamped = composeGridsWorldStamp(grids_, transforms_);
    if (stamped) {
      return stamped;
    }
    ROS_WARN_ONCE("world-stamp merge unavailable (rotation in init_pose); "
                  "falling back to OpenCV warp");
  }

  /* Pre-compute world bounding box for warp placement (RTAB grid.origin + init_pose). */
  double min_x = 0.0;
  double min_y = 0.0;
  const bool have_bounds =
      computeWorldBounds(grids_, transforms_, transforms_use_meters_, min_x, min_y);

  ROS_DEBUG("warping grids");
  internal::GridWarper warper;
  std::vector<cv::Mat> imgs_warped;
  imgs_warped.reserve(images_.size());
  std::vector<cv::Rect> rois;
  rois.reserve(images_.size());

  for (size_t i = 0; i < images_.size(); ++i) {
    if (!transforms_[i].empty() && !images_[i].empty()) {
      imgs_warped.emplace_back();
      cv::Mat warp_tf = transforms_use_meters_ && have_bounds
                            ? warpTransformForGrid(transforms_[i], grids_[i],
                                                   transforms_use_meters_, min_x,
                                                   min_y)
                            : transforms_[i];
      rois.emplace_back(
          warper.warp(images_[i], warp_tf, imgs_warped.back()));
    }
  }

  if (imgs_warped.empty()) {
    return nullptr;
  }

  ROS_DEBUG("compositing result grid");
  nav_msgs::OccupancyGrid::Ptr result;
  internal::GridCompositor compositor;
  result = compositor.compose(imgs_warped, rois);

  // set correct resolution to output grid. use resolution of identity (works
  // for estimated trasforms), or any resolution (works for know_init_positions)
  // - in that case all resolutions should be the same.
  float any_resolution = 0.0;
  for (size_t i = 0; i < transforms_.size(); ++i) {
    if (!grids_[i]) {
      continue;
    }
    // check if this transform is the reference frame
    if (isIdentity(transforms_[i])) {
      result->info.resolution = grids_[i]->info.resolution;
      break;
    }
    any_resolution = grids_[i]->info.resolution;
  }
  if (result->info.resolution <= 0.f) {
    result->info.resolution = any_resolution;
  }

  /* 1 robot: /map origin must match /locobot_X/map (identity map->locobot_X/map TF). */
  if (imgs_warped.size() == 1) {
    for (size_t i = 0; i < grids_.size(); ++i) {
      if (!grids_[i] || grids_[i]->data.empty()) {
        continue;
      }
      result->info.origin = grids_[i]->info.origin;
      result->info.origin.orientation.w = 1.0;
      if (transforms_use_meters_ && !transforms_[i].empty()) {
        result->info.origin.position.x += transforms_[i].at<double>(0, 2);
        result->info.origin.position.y += transforms_[i].at<double>(1, 2);
      }
      ROS_DEBUG("merged map (single grid) origin=(%.3f, %.3f)",
                result->info.origin.position.x, result->info.origin.position.y);
      return result;
    }
  }

  /* Multi-grid: merged origin = world bbox min corner (same as warp bounds). */
  if (have_bounds) {
    result->info.origin.position.x = min_x;
    result->info.origin.position.y = min_y;
  } else {
    const double res = static_cast<double>(result->info.resolution);
    std::vector<cv::Point> corners;
    std::vector<cv::Size> sizes;
    for (const auto& roi : rois) {
      corners.push_back(roi.tl());
      sizes.push_back(roi.size());
    }
    const cv::Rect dst_roi = cv::detail::resultRoi(corners, sizes);
    result->info.origin.position.x = dst_roi.tl().x * res;
    result->info.origin.position.y = dst_roi.tl().y * res;
  }
  result->info.origin.orientation.w = 1.0;

  ROS_DEBUG(
      "merged map origin=(%.3f, %.3f) size=%ux%u res=%.3f transforms_use_meters=%d",
      result->info.origin.position.x, result->info.origin.position.y,
      result->info.width, result->info.height, result->info.resolution,
      transforms_use_meters_);

  return result;
}

std::vector<geometry_msgs::Transform> MergingPipeline::getTransforms() const
{
  std::vector<geometry_msgs::Transform> result;
  result.reserve(transforms_.size());

  for (auto& transform : transforms_) {
    if (transform.empty()) {
      result.emplace_back();
      continue;
    }

    ROS_ASSERT(transform.type() == CV_64F);
    geometry_msgs::Transform ros_transform;
    ros_transform.translation.x = transform.at<double>(0, 2);
    ros_transform.translation.y = transform.at<double>(1, 2);
    ros_transform.translation.z = 0.;

    // our rotation is in fact only 2D, thus quaternion can be simplified
    double a = transform.at<double>(0, 0);
    double b = transform.at<double>(1, 0);
    ros_transform.rotation.w = std::sqrt(2. + 2. * a) * 0.5;
    ros_transform.rotation.x = 0.;
    ros_transform.rotation.y = 0.;
    ros_transform.rotation.z = std::copysign(std::sqrt(2. - 2. * a) * 0.5, b);

    result.push_back(ros_transform);
  }

  return result;
}

}  // namespace combine_grids
