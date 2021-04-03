const path = require("path");
const webpack = require("webpack");
const pixrem = require("pixrem");
const autoprefixer = require("autoprefixer");
const TerserPlugin = require("terser-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");

const SOURCE_DIR = "paper_uploads/static/paper_uploads/src";
const DIST_DIR = "paper_uploads/static/paper_uploads/dist";


module.exports = {
    devtool: "source-map",
    mode: "production",
    entry: {
        widget: path.resolve(`${SOURCE_DIR}/js/widget.js`),
    },
    output: {
        clean: true,
        path: path.resolve(`${DIST_DIR}`),
        publicPath: "/static/paper_uploads/dist/",
        filename: "[name].min.js",
        assetModuleFilename: "assets/[name][ext][query]"
    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /(node_modules|bower_components)/,
                use: [
                    {
                        loader: "babel-loader",
                        options: {
                            cacheDirectory: "cache"
                        }
                    }
                ]
            },
            {
                test: /\.css$/,
                use: [{
                    loader: MiniCssExtractPlugin.loader,
                }, {
                    loader: "fast-css-loader"
                }]
            },
            {
                test: /\.scss$/,
                use: [{
                    loader: MiniCssExtractPlugin.loader,
                },
                {
                    loader: "fast-css-loader",
                    options: {
                        importLoaders: 2
                    }
                },
                {
                    loader: "postcss-loader",
                    options: {
                        postcssOptions: {
                            plugins: [
                                pixrem(),
                                autoprefixer()
                            ]
                        }
                    }
                },
                {
                    loader: "sass-loader",
                    options: {
                        sassOptions: {
                            includePaths: [
                                path.resolve(`${SOURCE_DIR}/css/`)
                            ]
                        }
                    }
                }]
            },
            {
                test: /\.(jpe?g|png|gif|woff2?|ttf|eot|svg)$/i,
                type: "asset/resource",
            }
        ]
    },
    resolve: {
        modules: [SOURCE_DIR, "node_modules"],
    },
    plugins: [
        new webpack.ProgressPlugin(),
        new MiniCssExtractPlugin({
            filename: "[name].min.css",
        }),
    ],
    optimization: {
        moduleIds: "deterministic",
        minimizer: [
            new TerserPlugin({

            }),
            new CssMinimizerPlugin({

            })
        ]
    }
};
